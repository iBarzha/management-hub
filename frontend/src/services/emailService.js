import emailjs from '@emailjs/browser';

class EmailService {
  constructor() {
    this.serviceId = process.env.REACT_APP_EMAILJS_SERVICE_ID;
    this.templateId = process.env.REACT_APP_EMAILJS_TEMPLATE_ID;
    this.publicKey = process.env.REACT_APP_EMAILJS_PUBLIC_KEY;
    this.initialized = false;
  }

  init() {
    if (this.serviceId && this.templateId && this.publicKey) {
      emailjs.init(this.publicKey);
      this.initialized = true;
      console.log('EmailJS initialized successfully');
    } else {
      console.warn('EmailJS configuration missing. Email notifications will be disabled.');
    }
  }

  async sendNotificationEmail(notification, userEmail) {
    if (!this.initialized) {
      console.warn('EmailJS not initialized. Skipping email notification.');
      return false;
    }

    try {
      const templateParams = {
        to_email: userEmail,
        to_name: notification.user_name || 'User',
        notification_title: notification.title,
        notification_message: notification.message,
        notification_type: this.formatNotificationType(notification.notification_type),
        created_at: this.formatDate(notification.created_at),
        project_name: notification.project_name || 'Unknown Project',
        task_name: notification.task_name || '',
        app_url: window.location.origin,
      };

      const response = await emailjs.send(
        this.serviceId,
        this.templateId,
        templateParams
      );

      console.log('Email notification sent successfully:', response);
      return true;
    } catch (error) {
      console.error('Failed to send email notification:', error);
      return false;
    }
  }

  async sendBulkNotificationEmails(notifications, userEmails) {
    if (!this.initialized) {
      console.warn('EmailJS not initialized. Skipping bulk email notifications.');
      return [];
    }

    const results = [];
    
    for (const notification of notifications) {
      for (const email of userEmails) {
        try {
          const result = await this.sendNotificationEmail(notification, email);
          results.push({ notification: notification.id, email, success: result });
          
          // Add small delay to avoid rate limiting
          await new Promise(resolve => setTimeout(resolve, 100));
        } catch (error) {
          console.error(`Failed to send email to ${email}:`, error);
          results.push({ notification: notification.id, email, success: false, error: error.message });
        }
      }
    }

    return results;
  }

  async sendTaskAssignmentEmail(taskData, assigneeEmail) {
    if (!this.initialized) {
      console.warn('EmailJS not initialized. Skipping task assignment email.');
      return false;
    }

    const notification = {
      title: `New Task Assigned: ${taskData.title}`,
      message: `You have been assigned a new task in ${taskData.project_name}. 
                Priority: ${taskData.priority}
                Due Date: ${taskData.due_date || 'Not set'}
                Description: ${taskData.description || 'No description provided'}`,
      notification_type: 'task_assigned',
      created_at: new Date().toISOString(),
      project_name: taskData.project_name,
      task_name: taskData.title,
      user_name: taskData.assignee_name
    };

    return await this.sendNotificationEmail(notification, assigneeEmail);
  }

  async sendDeadlineReminderEmail(taskData, userEmail) {
    if (!this.initialized) {
      console.warn('EmailJS not initialized. Skipping deadline reminder email.');
      return false;
    }

    const notification = {
      title: `Deadline Reminder: ${taskData.title}`,
      message: `Task "${taskData.title}" is due soon in ${taskData.project_name}.
                Due Date: ${taskData.due_date}
                Priority: ${taskData.priority}
                Current Status: ${taskData.status}`,
      notification_type: 'deadline_reminder',
      created_at: new Date().toISOString(),
      project_name: taskData.project_name,
      task_name: taskData.title,
      user_name: taskData.user_name
    };

    return await this.sendNotificationEmail(notification, userEmail);
  }

  async sendProjectUpdateEmail(projectData, teamEmails) {
    if (!this.initialized) {
      console.warn('EmailJS not initialized. Skipping project update email.');
      return [];
    }

    const notification = {
      title: `Project Update: ${projectData.name}`,
      message: `The project "${projectData.name}" has been updated.
                Status: ${projectData.status}
                ${projectData.update_message || ''}`,
      notification_type: 'project_updated',
      created_at: new Date().toISOString(),
      project_name: projectData.name,
      task_name: '',
      user_name: 'Team Member'
    };

    const results = [];
    for (const email of teamEmails) {
      const result = await this.sendNotificationEmail(notification, email);
      results.push({ email, success: result });
      
      // Add small delay to avoid rate limiting
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    return results;
  }

  formatNotificationType(type) {
    return type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
  }

  // Check if email notifications are enabled for user
  isEmailNotificationEnabled(userPreferences, notificationType) {
    if (!userPreferences || !userPreferences.email_notifications) {
      return false;
    }

    const emailSettings = userPreferences.email_notifications;
    
    // Check global email notification setting
    if (!emailSettings.enabled) {
      return false;
    }

    // Check specific notification type settings
    switch (notificationType) {
      case 'task_assigned':
        return emailSettings.task_assignments || false;
      case 'task_updated':
        return emailSettings.task_updates || false;
      case 'project_updated':
        return emailSettings.project_updates || false;
      case 'deadline_reminder':
        return emailSettings.deadline_reminders || false;
      case 'mention':
        return emailSettings.mentions || false;
      case 'comment_added':
        return emailSettings.comments || false;
      default:
        return emailSettings.other || false;
    }
  }

  // Get email template for different notification types
  getEmailTemplate(notificationType) {
    const templates = {
      task_assigned: {
        subject: 'New Task Assignment - {{task_name}}',
        template: 'task_assignment'
      },
      task_updated: {
        subject: 'Task Update - {{task_name}}',
        template: 'task_update'
      },
      project_updated: {
        subject: 'Project Update - {{project_name}}',
        template: 'project_update'
      },
      deadline_reminder: {
        subject: 'Deadline Reminder - {{task_name}}',
        template: 'deadline_reminder'
      },
      mention: {
        subject: 'You were mentioned in {{project_name}}',
        template: 'mention'
      },
      comment_added: {
        subject: 'New Comment - {{task_name}}',
        template: 'comment'
      }
    };

    return templates[notificationType] || {
      subject: 'Project Management Hub Notification',
      template: 'general'
    };
  }
}

// Create singleton instance
const emailService = new EmailService();

export default emailService;