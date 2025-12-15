// Vaal AI Empire - Main JavaScript

// Smooth scrolling for anchor links
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

// Form submission tracking
const form = document.querySelector('form[name="demo-request"]');
if (form) {
    form.addEventListener('submit', function(e) {
        // Track form submission (Google Analytics if configured)
        if (typeof gtag !== 'undefined') {
            gtag('event', 'form_submission', {
                'event_category': 'Demo Request',
                'event_label': 'Early Access',
                'value': 1
            });
        }
        
        console.log('Demo request submitted');
    });
}

// Add active class to nav on scroll
window.addEventListener('scroll', function() {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('nav a[href^="#"]');
    
    let current = '';
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.clientHeight;
        if (scrollY >= (sectionTop - 200)) {
            current = section.getAttribute('id');
        }
    });
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === '#' + current) {
            link.classList.add('active');
        }
    });
});

// Console message for developers
console.log('%c⚡ Vaal AI Empire', 'color: #f7b731; font-size: 24px; font-weight: bold;');
console.log('%cBuilt in the Vaal. Built for Africa. Built to dominate.', 'color: #16213e; font-size: 14px;');
console.log('%cInterested in joining our team? Email: founders@vaalai.co.za', 'color: #666; font-size: 12px;');