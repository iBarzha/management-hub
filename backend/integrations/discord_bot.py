import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import discord
from discord.ext import commands
from django.conf import settings
from django.utils import timezone as django_timezone
from asgiref.sync import sync_to_async

from .models import (
    DiscordIntegration, DiscordChannel, DiscordMessage, 
    DiscordCommand, DiscordRole
)
from tasks.models import Task
from projects.models import Project
from users.models import User

logger = logging.getLogger(__name__)


class DiscordBot(commands.Bot):
    """Discord bot for project management integration"""
    
    def __init__(self, integration_id: int):
        self.integration_id = integration_id
        self.integration = None
        
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            description='Project Management Hub Discord Bot'
        )
        
        # Setup command handlers
        self.setup_commands()
    
    async def setup_hook(self):
        """Called when the bot is starting up"""
        self.integration = await sync_to_async(
            DiscordIntegration.objects.get
        )(id=self.integration_id)
        logger.info(f"Bot starting for guild: {self.integration.guild_name}")
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f'Discord bot logged in as {self.user} (ID: {self.user.id})')
        
        # Sync channels and roles
        await self.sync_guild_data()
    
    async def sync_guild_data(self):
        """Sync Discord guild data with database"""
        if not self.integration:
            return
            
        guild = self.get_guild(int(self.integration.guild_id))
        if not guild:
            logger.error(f"Guild {self.integration.guild_id} not found")
            return
        
        # Sync channels
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                await self.sync_channel(channel)
        
        # Sync roles
        for role in guild.roles:
            await self.sync_role(role)
    
    async def sync_channel(self, channel: discord.TextChannel):
        """Sync a Discord channel with database"""
        channel_data = {
            'channel_name': channel.name,
            'channel_type': 'text',
            'parent_id': str(channel.category.id) if channel.category else None,
            'position': channel.position,
            'nsfw': channel.nsfw,
        }
        
        await sync_to_async(DiscordChannel.objects.update_or_create)(
            integration=self.integration,
            channel_id=str(channel.id),
            defaults=channel_data
        )
    
    async def sync_role(self, role: discord.Role):
        """Sync a Discord role with database"""
        role_data = {
            'role_name': role.name,
            'color': f"#{role.color.value:06x}",
            'permissions': role.permissions.value,
            'position': role.position,
            'mentionable': role.mentionable,
            'hoisted': role.hoist,
            'managed': role.managed,
        }
        
        await sync_to_async(DiscordRole.objects.update_or_create)(
            integration=self.integration,
            role_id=str(role.id),
            defaults=role_data
        )
    
    def setup_commands(self):
        """Setup bot commands"""
        
        @self.command(name='tasks')
        async def list_tasks(ctx, status: str = 'all'):
            """List tasks with optional status filter"""
            await self.handle_tasks_command(ctx, status)
        
        @self.command(name='create-task')
        async def create_task(ctx, *, title: str):
            """Create a new task"""
            await self.handle_create_task_command(ctx, title)
        
        @self.command(name='assign')
        async def assign_task(ctx, user: discord.Member, task_id: int):
            """Assign a task to a user"""
            await self.handle_assign_task_command(ctx, user, task_id)
        
        @self.command(name='project-status')
        async def project_status(ctx, *, project_name: str):
            """Get project status overview"""
            await self.handle_project_status_command(ctx, project_name)
        
        @self.command(name='sprint')
        async def current_sprint(ctx):
            """Get current sprint information"""
            await self.handle_sprint_command(ctx)
        
        @self.command(name='standup')
        async def standup_reminder(ctx):
            """Send daily standup reminder"""
            await self.handle_standup_command(ctx)
        
        @self.command(name='help-pm')
        async def help_command(ctx):
            """Show available commands"""
            await self.handle_help_command(ctx)
    
    async def handle_tasks_command(self, ctx, status: str):
        """Handle !tasks command"""
        try:
            # Get project associated with channel
            channel_obj = await sync_to_async(DiscordChannel.objects.get)(
                integration=self.integration,
                channel_id=str(ctx.channel.id)
            )
            
            if not channel_obj.project:
                await ctx.send("❌ This channel is not associated with a project.")
                return
            
            # Filter tasks by status
            tasks_queryset = Task.objects.filter(project=channel_obj.project)
            
            if status != 'all':
                tasks_queryset = tasks_queryset.filter(status=status)
            
            tasks = await sync_to_async(list)(tasks_queryset[:10])  # Limit to 10
            
            if not tasks:
                await ctx.send(f"📝 No tasks found with status: {status}")
                return
            
            embed = discord.Embed(
                title=f"📋 Tasks ({status})",
                color=self.get_status_color(status),
                timestamp=datetime.now(timezone.utc)
            )
            
            for task in tasks:
                priority_emoji = self.get_priority_emoji(task.priority)
                embed.add_field(
                    name=f"{priority_emoji} {task.title}",
                    value=f"**Status:** {task.status}\n**Assignee:** {task.assignee.email if task.assignee else 'Unassigned'}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
            # Log command usage
            await self.log_command_usage('tasks')
            
        except DiscordChannel.DoesNotExist:
            await ctx.send("❌ Channel not found in database.")
        except Exception as e:
            logger.error(f"Error in tasks command: {e}")
            await ctx.send("❌ An error occurred while fetching tasks.")
    
    async def handle_create_task_command(self, ctx, title: str):
        """Handle !create-task command"""
        try:
            # Get project associated with channel
            channel_obj = await sync_to_async(DiscordChannel.objects.get)(
                integration=self.integration,
                channel_id=str(ctx.channel.id)
            )
            
            if not channel_obj.project:
                await ctx.send("❌ This channel is not associated with a project.")
                return
            
            # Create task
            task = await sync_to_async(Task.objects.create)(
                title=title,
                project=channel_obj.project,
                status='todo',
                priority='medium',
                created_by_id=self.integration.user_id
            )
            
            embed = discord.Embed(
                title="✅ Task Created",
                description=f"**{task.title}**",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="ID", value=task.id, inline=True)
            embed.add_field(name="Status", value=task.status, inline=True)
            embed.add_field(name="Priority", value=task.priority, inline=True)
            
            await ctx.send(embed=embed)
            
            # Log command usage
            await self.log_command_usage('create-task')
            
        except DiscordChannel.DoesNotExist:
            await ctx.send("❌ Channel not found in database.")
        except Exception as e:
            logger.error(f"Error in create-task command: {e}")
            await ctx.send("❌ An error occurred while creating the task.")
    
    async def handle_assign_task_command(self, ctx, user: discord.Member, task_id: int):
        """Handle !assign command"""
        try:
            # Get task
            task = await sync_to_async(Task.objects.get)(id=task_id)
            
            # Find user in database
            try:
                assignee = await sync_to_async(User.objects.get)(discord_user_id=str(user.id))
            except User.DoesNotExist:
                await ctx.send(f"❌ User {user.mention} is not linked to the project management system.")
                return
            
            # Assign task
            task.assignee = assignee
            await sync_to_async(task.save)()
            
            embed = discord.Embed(
                title="👤 Task Assigned",
                description=f"**{task.title}** has been assigned to {user.mention}",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            await ctx.send(embed=embed)
            
            # Log command usage
            await self.log_command_usage('assign')
            
        except Task.DoesNotExist:
            await ctx.send(f"❌ Task with ID {task_id} not found.")
        except Exception as e:
            logger.error(f"Error in assign command: {e}")
            await ctx.send("❌ An error occurred while assigning the task.")
    
    async def handle_project_status_command(self, ctx, project_name: str):
        """Handle !project-status command"""
        try:
            # Find project
            project = await sync_to_async(Project.objects.get)(name__icontains=project_name)
            
            # Get task statistics
            total_tasks = await sync_to_async(Task.objects.filter(project=project).count)()
            completed_tasks = await sync_to_async(Task.objects.filter(project=project, status='done').count)()
            in_progress_tasks = await sync_to_async(Task.objects.filter(project=project, status='in_progress').count)()
            todo_tasks = await sync_to_async(Task.objects.filter(project=project, status='todo').count)()
            
            progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            embed = discord.Embed(
                title=f"📊 Project Status: {project.name}",
                description=project.description or "No description available",
                color=self.get_status_color(project.status),
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(name="📈 Progress", value=f"{progress:.1f}%", inline=True)
            embed.add_field(name="✅ Completed", value=completed_tasks, inline=True)
            embed.add_field(name="🔄 In Progress", value=in_progress_tasks, inline=True)
            embed.add_field(name="📝 To Do", value=todo_tasks, inline=True)
            embed.add_field(name="📊 Total Tasks", value=total_tasks, inline=True)
            embed.add_field(name="🏷️ Status", value=project.status.title(), inline=True)
            
            await ctx.send(embed=embed)
            
            # Log command usage
            await self.log_command_usage('project-status')
            
        except Project.DoesNotExist:
            await ctx.send(f"❌ Project '{project_name}' not found.")
        except Exception as e:
            logger.error(f"Error in project-status command: {e}")
            await ctx.send("❌ An error occurred while fetching project status.")
    
    async def handle_sprint_command(self, ctx):
        """Handle !sprint command"""
        await ctx.send("🏃‍♂️ Sprint information feature coming soon!")
        await self.log_command_usage('sprint')
    
    async def handle_standup_command(self, ctx):
        """Handle !standup command"""
        try:
            # Get project associated with channel
            channel_obj = await sync_to_async(DiscordChannel.objects.get)(
                integration=self.integration,
                channel_id=str(ctx.channel.id)
            )
            
            if not channel_obj.project:
                await ctx.send("❌ This channel is not associated with a project.")
                return
            
            embed = discord.Embed(
                title="🗣️ Daily Standup Reminder",
                description=f"Time for the daily standup for **{channel_obj.project.name}**!",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="What to share:",
                value="• What did you accomplish yesterday?\n• What will you work on today?\n• Are there any blockers?",
                inline=False
            )
            
            await ctx.send(embed=embed)
            await self.log_command_usage('standup')
            
        except DiscordChannel.DoesNotExist:
            await ctx.send("❌ Channel not found in database.")
        except Exception as e:
            logger.error(f"Error in standup command: {e}")
            await ctx.send("❌ An error occurred while sending standup reminder.")
    
    async def handle_help_command(self, ctx):
        """Handle !help-pm command"""
        embed = discord.Embed(
            title="🤖 Project Management Bot Commands",
            description="Available commands for project management:",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        
        commands_help = [
            ("!tasks [status]", "List tasks (all, todo, in_progress, done)"),
            ("!create-task <title>", "Create a new task"),
            ("!assign @user <task_id>", "Assign a task to a user"),
            ("!project-status <name>", "Get project overview"),
            ("!sprint", "Current sprint information"),
            ("!standup", "Daily standup reminder"),
            ("!help-pm", "Show this help message"),
        ]
        
        for command, description in commands_help:
            embed.add_field(name=command, value=description, inline=False)
        
        await ctx.send(embed=embed)
    
    def get_status_color(self, status: str) -> discord.Color:
        """Get color based on status"""
        color_map = {
            'todo': discord.Color.light_grey(),
            'in_progress': discord.Color.yellow(),
            'done': discord.Color.green(),
            'active': discord.Color.green(),
            'completed': discord.Color.blue(),
            'on_hold': discord.Color.orange(),
        }
        return color_map.get(status, discord.Color.default())
    
    def get_priority_emoji(self, priority: str) -> str:
        """Get emoji based on priority"""
        emoji_map = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🔴',
            'urgent': '🚨',
        }
        return emoji_map.get(priority, '⚪')
    
    async def log_command_usage(self, command_name: str):
        """Log command usage"""
        try:
            command_obj, created = await sync_to_async(DiscordCommand.objects.get_or_create)(
                integration=self.integration,
                command_name=command_name,
                defaults={
                    'command_type': 'prefix',
                    'description': f"Command: {command_name}",
                    'enabled': True,
                }
            )
            command_obj.usage_count += 1
            command_obj.last_used = django_timezone.now()
            await sync_to_async(command_obj.save)()
        except Exception as e:
            logger.error(f"Error logging command usage: {e}")


class DiscordBotManager:
    """Manager for Discord bot instances"""
    
    def __init__(self):
        self.bots: Dict[int, DiscordBot] = {}
    
    async def start_bot(self, integration_id: int) -> bool:
        """Start a Discord bot for an integration"""
        try:
            integration = await sync_to_async(DiscordIntegration.objects.get)(id=integration_id)
            
            if integration_id in self.bots:
                logger.info(f"Bot already running for integration {integration_id}")
                return True
            
            bot = DiscordBot(integration_id)
            self.bots[integration_id] = bot
            
            # Start bot in background task
            asyncio.create_task(bot.start(integration.bot_token))
            
            logger.info(f"Started Discord bot for guild: {integration.guild_name}")
            return True
            
        except DiscordIntegration.DoesNotExist:
            logger.error(f"Discord integration {integration_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error starting Discord bot: {e}")
            return False
    
    async def stop_bot(self, integration_id: int) -> bool:
        """Stop a Discord bot"""
        if integration_id not in self.bots:
            return False
        
        try:
            bot = self.bots[integration_id]
            await bot.close()
            del self.bots[integration_id]
            logger.info(f"Stopped Discord bot for integration {integration_id}")
            return True
        except Exception as e:
            logger.error(f"Error stopping Discord bot: {e}")
            return False
    
    async def send_notification(self, channel_id: str, embed_data: Dict[str, Any]) -> bool:
        """Send notification to a Discord channel"""
        try:
            # Find the bot that has access to this channel
            for bot in self.bots.values():
                channel = bot.get_channel(int(channel_id))
                if channel:
                    embed = discord.Embed(**embed_data)
                    await channel.send(embed=embed)
                    return True
            
            logger.warning(f"No bot found for channel {channel_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error sending Discord notification: {e}")
            return False


# Global bot manager instance
bot_manager = DiscordBotManager()