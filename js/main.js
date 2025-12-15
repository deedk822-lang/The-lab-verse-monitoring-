// Vaal AI Empire - Main JavaScript
// Handles animations, interactions, and dynamic content

// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Navbar background on scroll
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.style.background = 'rgba(15, 52, 96, 0.98)';
    } else {
        navbar.style.background = 'rgba(15, 52, 96, 0.95)';
    }
});

// Animate elements on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe all cards and features
document.querySelectorAll('.engine-card, .feature, .pricing-card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'all 0.6s ease';
    observer.observe(el);
});

// Stats counter animation
function animateCounter(element, target, duration = 2000) {
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = target;
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current);
        }
    }, 16);
}

// Demo video placeholder interaction
const videoPlaceholder = document.querySelector('.video-placeholder');
if (videoPlaceholder) {
    videoPlaceholder.addEventListener('click', () => {
        alert('Demo video coming soon! Check back on December 27, 2025.');
    });
}

// Mobile menu toggle (if you add hamburger menu)
const createMobileMenu = () => {
    const navContainer = document.querySelector('.nav-container');
    const navMenu = document.querySelector('.nav-menu');
    
    if (window.innerWidth <= 768) {
        const hamburger = document.createElement('div');
        hamburger.className = 'hamburger';
        hamburger.innerHTML = '☰';
        hamburger.style.cssText = 'font-size: 2rem; cursor: pointer; color: var(--primary);';
        
        hamburger.addEventListener('click', () => {
            navMenu.style.display = navMenu.style.display === 'flex' ? 'none' : 'flex';
            navMenu.style.flexDirection = 'column';
            navMenu.style.position = 'absolute';
            navMenu.style.top = '60px';
            navMenu.style.left = '0';
            navMenu.style.width = '100%';
            navMenu.style.background = 'var(--bg-dark)';
            navMenu.style.padding = '1rem';
        });
        
        if (!document.querySelector('.hamburger')) {
            navContainer.appendChild(hamburger);
        }
    }
};

window.addEventListener('resize', createMobileMenu);
createMobileMenu();

// Form validation (for future contact forms)
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Local storage for user preferences
function savePreference(key, value) {
    localStorage.setItem(`vaalai_${key}`, JSON.stringify(value));
}

function getPreference(key) {
    const value = localStorage.getItem(`vaalai_${key}`);
    return value ? JSON.parse(value) : null;
}

// Track page views (basic analytics)
if (!sessionStorage.getItem('vaalai_session')) {
    sessionStorage.setItem('vaalai_session', Date.now());
    console.log('⚡ New session started');
}

// Console message for developers
console.log(`
⚡ Vaal AI Empire
Built in the Vaal. Built for Africa.
Interested in our tech stack? Email: founders@vaalai.co.za
`);

// Export functions for use in other scripts
window.VaalAI = {
    validateEmail,
    savePreference,
    getPreference
};