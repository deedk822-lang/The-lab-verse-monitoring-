// Jira Setup Guide - Main JavaScript
// Global variables
let currentStep = 1;
let wizardData = {
    instanceType: '',
    managementType: '',
    projectType: '',
    template: '',
    projectName: '',
    projectKey: '',
    teamMembers: []
};

// Template data
const templates = {
    software: [
        { id: 'scrum', name: 'Scrum', description: 'Agile development with sprints and backlogs', category: 'Development' },
        { id: 'kanban', name: 'Kanban', description: 'Continuous flow development', category: 'Development' },
        { id: 'bug-tracking', name: 'Bug Tracking', description: 'Track and manage software bugs', category: 'Development' },
        { id: 'devops', name: 'DevOps', description: 'Development and operations workflow', category: 'Development' }
    ],
    service: [
        { id: 'it-support', name: 'IT Support', description: 'Internal IT service management', category: 'Service' },
        { id: 'help-desk', name: 'Help Desk', description: 'Customer support and ticketing', category: 'Service' },
        { id: 'facilities', name: 'Facilities', description: 'Facilities management requests', category: 'Service' },
        { id: 'hr-service', name: 'HR Service', description: 'Human resources service requests', category: 'Service' }
    ],
    work: [
        { id: 'project-management', name: 'Project Management', description: 'General project tracking and management', category: 'Business' },
        { id: 'task-tracking', name: 'Task Tracking', description: 'Simple task and to-do management', category: 'Business' },
        { id: 'marketing', name: 'Marketing', description: 'Marketing campaign management', category: 'Business' },
        { id: 'event-planning', name: 'Event Planning', description: 'Event coordination and planning', category: 'Business' }
    ],
    discovery: [
        { id: 'product-roadmap', name: 'Product Roadmap', description: 'Product strategy and roadmap planning', category: 'Product' },
        { id: 'idea-management', name: 'Idea Management', description: 'Collect and prioritize ideas', category: 'Product' },
        { id: 'competitive-analysis', name: 'Competitive Analysis', description: 'Track competitors and market analysis', category: 'Product' },
        { id: 'user-research', name: 'User Research', description: 'Manage user feedback and research', category: 'Product' }
    ]
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeAnimations();
    loadWizardState();
});

// Animation initialization
function initializeAnimations() {
    // Animate feature cards on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                anime({
                    targets: entry.target,
                    opacity: [0, 1],
                    translateY: [20, 0],
                    duration: 600,
                    easing: 'easeOutQuad'
                });
            }
        });
    }, observerOptions);

    // Observe all feature cards
    document.querySelectorAll('.card-hover').forEach(card => {
        card.style.opacity = '0';
        observer.observe(card);
    });
}

// Wizard functionality
function openWizard() {
    document.getElementById('wizardModal').classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    currentStep = 1;
    updateWizardStep();
    
    // Animate modal entrance
    anime({
        targets: '#wizardModal .bg-white',
        scale: [0.8, 1],
        opacity: [0, 1],
        duration: 300,
        easing: 'easeOutBack'
    });
}

function closeWizard() {
    anime({
        targets: '#wizardModal .bg-white',
        scale: [1, 0.8],
        opacity: [1, 0],
        duration: 200,
        easing: 'easeInQuad',
        complete: () => {
            document.getElementById('wizardModal').classList.add('hidden');
            document.body.style.overflow = 'auto';
        }
    });
    saveWizardState();
}

function nextStep() {
    if (validateCurrentStep()) {
        currentStep++;
        updateWizardStep();
        
        // Animate step transition
        const currentStepEl = document.querySelector('.wizard-step.active');
        const nextStepEl = document.getElementById(`step${currentStep}`);
        
        anime({
            targets: currentStepEl,
            opacity: [1, 0],
            translateX: [-20, 0],
            duration: 200,
            complete: () => {
                currentStepEl.classList.remove('active');
                nextStepEl.classList.add('active');
                anime({
                    targets: nextStepEl,
                    opacity: [0, 1],
                    translateX: [20, 0],
                    duration: 300
                });
            }
        });
    }
}

function previousStep() {
    if (currentStep > 1) {
        currentStep--;
        updateWizardStep();
        
        // Animate step transition
        const currentStepEl = document.querySelector('.wizard-step.active');
        const prevStepEl = document.getElementById(`step${currentStep}`);
        
        anime({
            targets: currentStepEl,
            opacity: [1, 0],
            translateX: [20, 0],
            duration: 200,
            complete: () => {
                currentStepEl.classList.remove('active');
                prevStepEl.classList.add('active');
                anime({
                    targets: prevStepEl,
                    opacity: [0, 1],
                    translateX: [-20, 0],
                    duration: 300
                });
            }
        });
    }
}

function updateWizardStep() {
    // Update progress bar
    const progress = (currentStep / 6) * 100;
    document.getElementById('progressBar').style.width = `${progress}%`;
    document.getElementById('currentStep').textContent = currentStep;
    document.getElementById('progressPercent').textContent = `${Math.round(progress)}%`;
    
    // Update navigation buttons
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    
    if (currentStep === 1) {
        prevBtn.classList.add('hidden');
    } else {
        prevBtn.classList.remove('hidden');
    }
    
    if (currentStep === 6) {
        nextBtn.textContent = 'Complete Setup';
        nextBtn.onclick = completeSetup;
        generateSummary();
    } else {
        nextBtn.textContent = 'Next Step';
        nextBtn.onclick = nextStep;
    }
    
    // Load step-specific content
    if (currentStep === 4) {
        loadTemplates();
    }
}

function validateCurrentStep() {
    switch (currentStep) {
        case 1:
            if (!wizardData.instanceType) {
                showNotification('Please select an instance type', 'warning');
                return false;
            }
            break;
        case 2:
            if (!wizardData.managementType) {
                showNotification('Please select a management type', 'warning');
                return false;
            }
            break;
        case 3:
            if (!wizardData.projectType) {
                showNotification('Please select a project type', 'warning');
                return false;
            }
            break;
        case 4:
            if (!wizardData.template) {
                showNotification('Please select a template', 'warning');
                return false;
            }
            break;
        case 5:
            const projectName = document.getElementById('projectName').value;
            if (!projectName.trim()) {
                showNotification('Please enter a project name', 'warning');
                return false;
            }
            wizardData.projectName = projectName;
            wizardData.projectKey = document.getElementById('projectKey').value || generateProjectKey(projectName);
            break;
    }
    return true;
}

// Selection functions
function selectInstanceType(type) {
    wizardData.instanceType = type;
    updateSelection('step1', type);
    setTimeout(() => nextStep(), 500);
}

function selectManagementType(type) {
    wizardData.managementType = type;
    updateSelection('step2', type);
    setTimeout(() => nextStep(), 500);
}

function selectProjectType(type) {
    wizardData.projectType = type;
    updateSelection('step3', type);
    setTimeout(() => nextStep(), 500);
}

function selectTemplate(templateId) {
    wizardData.template = templateId;
    updateTemplateSelection(templateId);
    setTimeout(() => nextStep(), 500);
}

function updateSelection(stepId, selectedValue) {
    const step = document.getElementById(stepId);
    const cards = step.querySelectorAll('.template-card');
    
    cards.forEach(card => {
        card.classList.remove('selected');
        if (card.onclick.toString().includes(selectedValue)) {
            card.classList.add('selected');
        }
    });
}

function updateTemplateSelection(templateId) {
    const cards = document.querySelectorAll('#templateGrid .template-card');
    cards.forEach(card => {
        card.classList.remove('selected');
        if (card.dataset.templateId === templateId) {
            card.classList.add('selected');
        }
    });
}

// Template management
function loadTemplates() {
    const projectType = wizardData.projectType;
    const templateList = templates[projectType] || [];
    const grid = document.getElementById('templateGrid');
    
    grid.innerHTML = templateList.map(template => `
        <div class="template-card p-4 rounded-xl cursor-pointer" data-template-id="${template.id}" onclick="selectTemplate('${template.id}')">
            <div class="flex items-center mb-3">
                <div class="w-10 h-10 bg-teal-100 rounded-lg flex items-center justify-center mr-3">
                    <svg class="w-5 h-5 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                </div>
                <div>
                    <h4 class="font-semibold text-gray-900">${template.name}</h4>
                    <span class="text-xs text-teal-600 bg-teal-100 px-2 py-1 rounded-full">${template.category}</span>
                </div>
            </div>
            <p class="text-sm text-gray-600">${template.description}</p>
        </div>
    `).join('');
}

function filterTemplates() {
    const searchTerm = document.getElementById('templateSearch').value.toLowerCase();
    const cards = document.querySelectorAll('#templateGrid .template-card');
    
    cards.forEach(card => {
        const templateName = card.querySelector('h4').textContent.toLowerCase();
        const templateDesc = card.querySelector('p').textContent.toLowerCase();
        
        if (templateName.includes(searchTerm) || templateDesc.includes(searchTerm)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// Team management
function addTeamMember() {
    const container = document.querySelector('#step5 .space-y-2');
    const newMember = document.createElement('div');
    newMember.className = 'flex items-center space-x-2';
    newMember.innerHTML = `
        <input type="email" class="flex-1 px-4 py-2 border border-gray-300 rounded-lg" placeholder="teammate@company.com">
        <select class="px-4 py-2 border border-gray-300 rounded-lg">
            <option>Admin</option>
            <option>Developer</option>
            <option>Viewer</option>
        </select>
        <button onclick="removeTeamMember(this)" class="text-red-600 hover:text-red-800">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
            </svg>
        </button>
    `;
    container.insertBefore(newMember, container.lastElementChild);
}

function removeTeamMember(button) {
    button.closest('.flex').remove();
}

// Utility functions
function generateProjectKey(projectName) {
    return projectName.toUpperCase()
        .replace(/[^A-Z0-9]/g, '')
        .substring(0, 5) || 'PROJ';
}

function generateSummary() {
    const selectedTemplate = templates[wizardData.projectType]?.find(t => t.id === wizardData.template);
    
    const summaryHTML = `
        <div class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <h5 class="font-semibold text-gray-700">Instance Type</h5>
                    <p class="text-gray-600 capitalize">${wizardData.instanceType}</p>
                </div>
                <div>
                    <h5 class="font-semibold text-gray-700">Management Type</h5>
                    <p class="text-gray-600">${wizardData.managementType.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}</p>
                </div>
                <div>
                    <h5 class="font-semibold text-gray-700">Project Type</h5>
                    <p class="text-gray-600 capitalize">${wizardData.projectType.replace('-', ' ')}</p>
                </div>
                <div>
                    <h5 class="font-semibold text-gray-700">Template</h5>
                    <p class="text-gray-600">${selectedTemplate?.name || 'Custom'}</p>
                </div>
            </div>
            <div>
                <h5 class="font-semibold text-gray-700">Project Details</h5>
                <p class="text-gray-600">Name: ${wizardData.projectName}</p>
                <p class="text-gray-600">Key: ${wizardData.projectKey}</p>
            </div>
        </div>
    `;
    
    document.getElementById('summaryContent').innerHTML = summaryHTML;
}

function completeSetup() {
    // Save setup completion
    localStorage.setItem('jiraSetupComplete', JSON.stringify({
        ...wizardData,
        completedAt: new Date().toISOString()
    }));
    
    // Show completion animation
    anime({
        targets: '#wizardModal .bg-white',
        scale: [1, 1.05, 1],
        duration: 600,
        easing: 'easeInOutQuad'
    });
    
    showNotification('Setup configuration saved! Check your email for next steps.', 'success');
    
    setTimeout(() => {
        closeWizard();
        // Redirect to checklist page
        window.location.href = 'checklist.html';
    }, 2000);
}

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-20 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm ${
        type === 'success' ? 'bg-green-500 text-white' :
        type === 'warning' ? 'bg-yellow-500 text-white' :
        type === 'error' ? 'bg-red-500 text-white' :
        'bg-blue-500 text-white'
    }`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Animate in
    anime({
        targets: notification,
        translateX: [300, 0],
        opacity: [0, 1],
        duration: 300,
        easing: 'easeOutQuad'
    });
    
    // Auto remove
    setTimeout(() => {
        anime({
            targets: notification,
            translateX: [0, 300],
            opacity: [1, 0],
            duration: 300,
            easing: 'easeInQuad',
            complete: () => notification.remove()
        });
    }, 4000);
}

// State management
function saveWizardState() {
    localStorage.setItem('jiraWizardState', JSON.stringify({
        currentStep,
        wizardData
    }));
}

function loadWizardState() {
    const saved = localStorage.getItem('jiraWizardState');
    if (saved) {
        const state = JSON.parse(saved);
        wizardData = state.wizardData;
        // Don't restore step, always start from beginning
    }
}

// Scroll functionality
function scrollToFeatures() {
    document.getElementById('features').scrollIntoView({
        behavior: 'smooth'
    });
}

// Project key auto-generation
document.addEventListener('DOMContentLoaded', function() {
    const projectNameInput = document.getElementById('projectName');
    const projectKeyInput = document.getElementById('projectKey');
    
    if (projectNameInput && projectKeyInput) {
        projectNameInput.addEventListener('input', function() {
            if (!projectKeyInput.value) {
                projectKeyInput.value = generateProjectKey(this.value);
            }
        });
    }
});

// Keyboard navigation
document.addEventListener('keydown', function(e) {
    if (document.getElementById('wizardModal').classList.contains('hidden')) {
        return;
    }
    
    if (e.key === 'Escape') {
        closeWizard();
    } else if (e.key === 'ArrowRight' && currentStep < 6) {
        nextStep();
    } else if (e.key === 'ArrowLeft' && currentStep > 1) {
        previousStep();
    }
});

// Analytics and tracking (placeholder)
function trackEvent(eventName, properties = {}) {
    // Placeholder for analytics tracking
    console.log('Track Event:', eventName, properties);
}

// Export for use in other modules
window.JiraSetupGuide = {
    openWizard,
    closeWizard,
    nextStep,
    previousStep,
    selectInstanceType,
    selectManagementType,
    selectProjectType,
    selectTemplate,
    showNotification,
    trackEvent
};