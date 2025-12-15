// Vaal AI Empire - Main JavaScript
// African Futurism meets Industrial Tech

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeAnimations();
    initializeCounters();
    initializeCharts();
    initializeNeuralNetwork();
    initializeTypedText();
    startEngineSimulations();
    initializePaymentSystem();
});

// Typed text animation for hero section
function initializeTypedText() {
    const typedElement = document.getElementById('typed-text');
    if (!typedElement) return;
    
    const typed = new Typed('#typed-text', {
        strings: [
            'Africa...',
            'we built the future.',
            'we built the Empire.'
        ],
        typeSpeed: 80,
        backSpeed: 50,
        backDelay: 2000,
        startDelay: 1000,
        loop: false,
        showCursor: true,
        cursorChar: '|',
        onComplete: function() {
            // Add glow effect when complete
            typedElement.classList.add('glow-text');
        }
    });
}

// Animate metric counters
function initializeCounters() {
    const counters = document.querySelectorAll('.stat-number[data-target]');
    
    const observerOptions = {
        threshold: 0.5,
        rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    counters.forEach(counter => observer.observe(counter));
}

function animateCounter(element) {
    const target = parseInt(element.dataset.target);
    const duration = 2000; // 2 seconds
    const increment = target / (duration / 16); // 60 FPS
    let current = 0;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        
        // Format based on size
        if (target >= 100) {
            element.textContent = Math.floor(current);
        } else {
            element.textContent = Math.floor(current);
        }
    }, 16);
}

// Initialize ECharts for engine visualizations
function initializeCharts() {
    // Only initialize if echarts is available
    if (typeof echarts === 'undefined') {
        console.log('ECharts not loaded, skipping chart initialization');
        return;
    }
    
    // Tax Recovery Chart
    const taxChartEl = document.getElementById('taxChart');
    if (taxChartEl) {
        const taxChart = echarts.init(taxChartEl);
        const taxOption = {
            backgroundColor: 'transparent',
            grid: { top: 10, right: 10, bottom: 20, left: 30 },
            xAxis: {
                type: 'category',
                data: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                axisLine: { lineStyle: { color: '#666' } },
                axisLabel: { color: '#999', fontSize: 10 }
            },
            yAxis: {
                type: 'value',
                axisLine: { lineStyle: { color: '#666' } },
                axisLabel: { color: '#999', fontSize: 10 },
                splitLine: { lineStyle: { color: '#333' } }
            },
            series: [{
                data: [12, 19, 25, 32, 41, 58],
                type: 'line',
                smooth: true,
                lineStyle: { color: '#00ff88', width: 2 },
                itemStyle: { color: '#00ff88' },
                areaStyle: {
                    color: {
                        type: 'linear',
                        x: 0, y: 0, x2: 0, y2: 1,
                        colorStops: [
                            { offset: 0, color: 'rgba(0,255,136,0.3)' },
                            { offset: 1, color: 'rgba(0,255,136,0.1)' }
                        ]
                    }
                }
            }]
        };
        taxChart.setOption(taxOption);
        window.addEventListener('resize', () => taxChart.resize());
    }
    
    // Crisis Detection Chart
    const crisisChartEl = document.getElementById('crisisChart');
    if (crisisChartEl) {
        const crisisChart = echarts.init(crisisChartEl);
        const crisisOption = {
            backgroundColor: 'transparent',
            grid: { top: 10, right: 10, bottom: 20, left: 30 },
            xAxis: {
                type: 'category',
                data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
                axisLine: { lineStyle: { color: '#666' } },
                axisLabel: { color: '#999', fontSize: 10 }
            },
            yAxis: {
                type: 'value',
                axisLine: { lineStyle: { color: '#666' } },
                axisLabel: { color: '#999', fontSize: 10 },
                splitLine: { lineStyle: { color: '#333' } }
            },
            series: [{
                data: [3, 7, 12, 8, 15, 6],
                type: 'bar',
                itemStyle: {
                    color: {
                        type: 'linear',
                        x: 0, y: 0, x2: 0, y2: 1,
                        colorStops: [
                            { offset: 0, color: '#ff6600' },
                            { offset: 1, color: '#ff9933' }
                        ]
                    }
                }
            }]
        };
        crisisChart.setOption(crisisOption);
        window.addEventListener('resize', () => crisisChart.resize());
    }
    
    // Talent Placement Chart
    const talentChartEl = document.getElementById('talentChart');
    if (talentChartEl) {
        const talentChart = echarts.init(talentChartEl);
        const talentOption = {
            backgroundColor: 'transparent',
            grid: { top: 10, right: 10, bottom: 20, left: 30 },
            xAxis: {
                type: 'category',
                data: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                axisLine: { lineStyle: { color: '#666' } },
                axisLabel: { color: '#999', fontSize: 10 }
            },
            yAxis: {
                type: 'value',
                axisLine: { lineStyle: { color: '#666' } },
                axisLabel: { color: '#999', fontSize: 10 },
                splitLine: { lineStyle: { color: '#333' } }
            },
            series: [{
                data: [8, 15, 23, 31],
                type: 'line',
                smooth: true,
                lineStyle: { color: '#9933ff', width: 2 },
                itemStyle: { color: '#9933ff' },
                areaStyle: {
                    color: {
                        type: 'linear',
                        x: 0, y: 0, x2: 0, y2: 1,
                        colorStops: [
                            { offset: 0, color: 'rgba(153,51,255,0.3)' },
                            { offset: 1, color: 'rgba(153,51,255,0.1)' }
                        ]
                    }
                }
            }]
        };
        talentChart.setOption(talentOption);
        window.addEventListener('resize', () => talentChart.resize());
    }
}

// Neural network visualization using p5.js
function initializeNeuralNetwork() {
    const networkContainer = document.getElementById('neuralNetwork');
    if (!networkContainer || typeof p5 === 'undefined') return;
    
    new p5((p) => {
        let nodes = [];
        let connections = [];
        
        p.setup = function() {
            const canvas = p.createCanvas(
                networkContainer.offsetWidth,
                networkContainer.offsetHeight
            );
            canvas.parent('neuralNetwork');
            
            // Create nodes
            for (let i = 0; i < 20; i++) {
                nodes.push({
                    x: p.random(p.width),
                    y: p.random(p.height),
                    vx: p.random(-1, 1),
                    vy: p.random(-1, 1),
                    size: p.random(3, 8)
                });
            }
            
            // Create connections
            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const dist = p.dist(nodes[i].x, nodes[i].y, nodes[j].x, nodes[j].y);
                    if (dist < 150) {
                        connections.push({
                            from: i,
                            to: j,
                            strength: p.random(0.3, 1)
                        });
                    }
                }
            }
        };
        
        p.draw = function() {
            p.clear();
            
            // Update and draw nodes
            for (let node of nodes) {
                node.x += node.vx;
                node.y += node.vy;
                
                // Bounce off edges
                if (node.x < 0 || node.x > p.width) node.vx *= -1;
                if (node.y < 0 || node.y > p.height) node.vy *= -1;
                
                // Draw node
                p.fill(0, 102, 255, 150);
                p.noStroke();
                p.ellipse(node.x, node.y, node.size);
                
                // Draw glow
                p.fill(0, 102, 255, 50);
                p.ellipse(node.x, node.y, node.size * 2);
            }
            
            // Draw connections
            for (let conn of connections) {
                const from = nodes[conn.from];
                const to = nodes[conn.to];
                p.stroke(0, 102, 255, conn.strength * 100);
                p.strokeWeight(conn.strength * 2);
                p.line(from.x, from.y, to.x, to.y);
                
                // Animate connection strength
                conn.strength += p.random(-0.05, 0.05);
                conn.strength = p.constrain(conn.strength, 0.1, 1);
            }
        };
        
        p.windowResized = function() {
            p.resizeCanvas(networkContainer.offsetWidth, networkContainer.offsetHeight);
        };
    });
}

// Engine simulations and animations
function startEngineSimulations() {
    // Simulate self-healing log updates
    const logElement = document.getElementById('healingLog');
    if (logElement) {
        const messages = [
            'System health check completed. All systems nominal.',
            'Optimizing neural network parameters...',
            'Updating SARS regulation database...',
            'Processing GDELT data streams...',
            'Validating developer skill assessments...'
        ];
        
        setInterval(() => {
            const timestamp = new Date().toLocaleTimeString();
            const randomMessage = messages[Math.floor(Math.random() * messages.length)];
            logElement.innerHTML = `[${timestamp}] ${randomMessage}`;
        }, 3000);
    }
}

// Initialize general animations
function initializeAnimations() {
    // Add fade-in animation to sections on scroll
    const sections = document.querySelectorAll('section');
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
    
    sections.forEach(section => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(20px)';
        section.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(section);
    });
}

// Payment System Integration
function initializePaymentSystem() {
    const paymentForm = document.getElementById('paymentForm');
    if (paymentForm) {
        paymentForm.addEventListener('submit', handlePaymentSubmission);
    }
}

function handlePaymentSubmission(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    
    // Show processing state
    const submitButton = e.target.querySelector('button[type="submit"]');
    const originalText = submitButton.textContent;
    submitButton.textContent = 'Processing...';
    submitButton.disabled = true;
    
    // Simulate payment processing
    setTimeout(() => {
        alert('Payment form submitted successfully!');
        submitButton.textContent = originalText;
        submitButton.disabled = false;
        e.target.reset();
    }, 2000);
}

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

// Particle effect on button clicks
if (typeof anime !== 'undefined') {
    document.addEventListener('click', function(e) {
        if (e.target.tagName === 'BUTTON' || e.target.classList.contains('cta-button')) {
            createParticleEffect(e.clientX, e.clientY);
        }
    });
}

function createParticleEffect(x, y) {
    if (typeof anime === 'undefined') return;
    
    for (let i = 0; i < 5; i++) {
        const particle = document.createElement('div');
        particle.style.cssText = `
            position: fixed;
            left: ${x}px;
            top: ${y}px;
            width: 4px;
            height: 4px;
            background: #0066ff;
            border-radius: 50%;
            pointer-events: none;
            z-index: 9999;
        `;
        document.body.appendChild(particle);
        
        anime({
            targets: particle,
            translateX: (Math.random() - 0.5) * 100,
            translateY: (Math.random() - 0.5) * 100,
            opacity: [1, 0],
            scale: [1, 0],
            duration: 1000,
            easing: 'easeOutCubic',
            complete: () => particle.remove()
        });
    }
}

// Console easter egg
console.log(`
🚀 VAAL AI EMPIRE - SYSTEM ONLINE
=================================
Built in the Vaal Triangle
Built for Africa
Built to dominate

Digital sovereignty begins here.
`);

// Form tracking
const demoForm = document.querySelector('form[name="demo-request"]');
if (demoForm) {
    demoForm.addEventListener('submit', function() {
        console.log('Demo request submitted');
        if (typeof gtag !== 'undefined') {
            gtag('event', 'form_submission', {
                'event_category': 'Demo Request',
                'event_label': 'Early Access'
            });
        }
    });
}