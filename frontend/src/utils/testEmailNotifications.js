import emailService from '../services/emailService';

/**
 * Test utility functions for email notifications
 */

// Initialize email service for testing
export const initializeEmailService = () => {
  emailService.init();
  console.log('EmailJS service initialized for testing');
};

// Test basic notification email
export const testBasicNotification = async (userEmail = 'test@example.com') => {
  const testNotification = {
    id: 1,
    title: 'Test Notification',
    message: 'This is a test email notification from Project Management Hub.',
    notification_type: 'task_assigned',
    created_at: new Date().toISOString(),
    project_name: 'Test Project',
    task_name: 'Test Task',
    user_name: 'Test User'
  };

  try {
    const result = await emailService.sendNotificationEmail(testNotification, userEmail);
    console.log('Test email result:', result);
    return result;
  } catch (error) {
    console.error('Test email failed:', error);
    return false;
  }
};

// Test task assignment email
export const testTaskAssignmentEmail = async (userEmail = 'test@example.com') => {
  const taskData = {
    title: 'Complete Project Documentation',
    description: 'Write comprehensive documentation for the new features.',
    priority: 'High',
    due_date: '2024-02-15',
    project_name: 'Documentation Project',
    assignee_name: 'Test User'
  };

  try {
    const result = await emailService.sendTaskAssignmentEmail(taskData, userEmail);
    console.log('Task assignment email result:', result);
    return result;
  } catch (error) {
    console.error('Task assignment email failed:', error);
    return false;
  }
};

// Test deadline reminder email
export const testDeadlineReminderEmail = async (userEmail = 'test@example.com') => {
  const taskData = {
    title: 'Submit Monthly Report',
    due_date: '2024-02-01',
    priority: 'High',
    status: 'In Progress',
    project_name: 'Monthly Reports',
    user_name: 'Test User'
  };

  try {
    const result = await emailService.sendDeadlineReminderEmail(taskData, userEmail);
    console.log('Deadline reminder email result:', result);
    return result;
  } catch (error) {
    console.error('Deadline reminder email failed:', error);
    return false;
  }
};

// Test project update email
export const testProjectUpdateEmail = async (teamEmails = ['test@example.com']) => {
  const projectData = {
    name: 'New Feature Development',
    status: 'In Progress',
    update_message: 'The project has been updated with new requirements and timeline adjustments.'
  };

  try {
    const results = await emailService.sendProjectUpdateEmail(projectData, teamEmails);
    console.log('Project update email results:', results);
    return results;
  } catch (error) {
    console.error('Project update email failed:', error);
    return [];
  }
};

// Test email notification preferences
export const testEmailPreferences = () => {
  const testPreferences = {
    email_notifications: {
      enabled: true,
      task_assignments: true,
      task_updates: false,
      project_updates: true,
      deadline_reminders: true,
      mentions: true,
      comments: false,
      other: false
    }
  };

  console.log('Testing email preferences...');
  
  // Test different notification types
  const tests = [
    { type: 'task_assigned', expected: true },
    { type: 'task_updated', expected: false },
    { type: 'project_updated', expected: true },
    { type: 'deadline_reminder', expected: true },
    { type: 'mention', expected: true },
    { type: 'comment_added', expected: false },
    { type: 'other', expected: false }
  ];

  tests.forEach(test => {
    const result = emailService.isEmailNotificationEnabled(testPreferences, test.type);
    console.log(`${test.type}: ${result} (expected: ${test.expected}) - ${result === test.expected ? '✅' : '❌'}`);
  });
};

// Test all email functionality
export const runAllEmailTests = async (userEmail = 'test@example.com') => {
  console.log('🧪 Starting email notification tests...');
  console.log('📧 Test email:', userEmail);
  
  // Initialize service
  initializeEmailService();
  
  // Test preferences
  console.log('\n1️⃣ Testing email preferences...');
  testEmailPreferences();
  
  // Test basic notification
  console.log('\n2️⃣ Testing basic notification email...');
  await testBasicNotification(userEmail);
  
  // Add delay between tests
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // Test task assignment
  console.log('\n3️⃣ Testing task assignment email...');
  await testTaskAssignmentEmail(userEmail);
  
  // Add delay between tests
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // Test deadline reminder
  console.log('\n4️⃣ Testing deadline reminder email...');
  await testDeadlineReminderEmail(userEmail);
  
  // Add delay between tests
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // Test project update
  console.log('\n5️⃣ Testing project update email...');
  await testProjectUpdateEmail([userEmail]);
  
  console.log('\n✅ All email tests completed!');
  console.log('📧 Check your email inbox for test notifications.');
};

// Helper function to add test button to development builds
export const addTestButton = () => {
  if (process.env.NODE_ENV === 'development') {
    const testButton = document.createElement('button');
    testButton.textContent = '📧 Test Email Notifications';
    testButton.style.position = 'fixed';
    testButton.style.top = '10px';
    testButton.style.right = '10px';
    testButton.style.zIndex = '9999';
    testButton.style.padding = '10px';
    testButton.style.backgroundColor = '#2563eb';
    testButton.style.color = 'white';
    testButton.style.border = 'none';
    testButton.style.borderRadius = '5px';
    testButton.style.cursor = 'pointer';
    
    testButton.onclick = () => {
      const email = prompt('Enter test email address:', 'test@example.com');
      if (email) {
        runAllEmailTests(email);
      }
    };
    
    document.body.appendChild(testButton);
  }
};

export default {
  initializeEmailService,
  testBasicNotification,
  testTaskAssignmentEmail,
  testDeadlineReminderEmail,
  testProjectUpdateEmail,
  testEmailPreferences,
  runAllEmailTests,
  addTestButton
};