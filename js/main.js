// Vaal AI Empire - Main JavaScript
// African Futurism meets Industrial Tech

// Prevent multiple initializations
if (window.vaalEmpireInitialized) {
    console.warn("Vaal AI Empire already initialized.");
} else {
    window.vaalEmpireInitialized = true;

    // Initialize when DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
        try {
            initializeAnimations();
            initializeCounters();
            initializeCharts();
            initializeNeuralNetwork();
            initializeTypedText();
            startEngineSimulations();
            initializePaymentSystem();
            console.log("🚀 Vaal AI Empire Systems Online");
        } catch (e) {
            console.error("Initialization Error:", e);
        }
    });
}

// Typed text animation for hero section
function initializeTypedText() {
    if (!document.getElementById('typed-text')) return; // Safety check

    // Ensure Typed.js is loaded
    if (typeof Typed === 'undefined') {
        console.warn("Typed.js library missing.");
        return;
    }

    new Typed('#typed-text', {
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
            const el = document.getElementById('typed-text');
            if (el) el.classList.add('glow-text');
        }
    });
}

// Animate metric counters
function initializeCounters() {
    const counters = document.querySelectorAll('.metric-counter');
    if (counters.length === 0) return;

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
    if (isNaN(target)) return;

    const duration = 2000;
    const increment = target / (duration / 16);
    let current = 0;

    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }

        if (target >= 100) {
            element.textContent = Math.floor(current) + (target >= 500 ? 'K' : '+');
        } else {
            element.textContent = Math.floor(current);
        }
    }, 16);
}

// Initialize ECharts for engine visualizations
function initializeCharts() {
    if (typeof echarts === 'undefined') return;

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
            const canvas = p.createCanvas(networkContainer.offsetWidth, networkContainer.offsetHeight);
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
                        connections.push({ from: i, to: j, strength: p.random(0.3, 1) });
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
    // Only run if elements exist
    const taxElement = document.getElementById('taxRecovery');
    if (taxElement) {
        setInterval(() => {
            const currentValue = parseInt(taxElement.textContent.replace(/[RK,]/g, '')) || 0;
            const newValue = currentValue + Math.floor(Math.random() * 5000);
            taxElement.textContent = 'R' + newValue.toLocaleString();
        }, 5000);
    }

    const alertElement = document.getElementById('crisisAlerts');
    if (alertElement) {
        setInterval(() => {
            const currentValue = parseInt(alertElement.textContent) || 0;
            const newValue = currentValue + Math.floor(Math.random() * 3);
            alertElement.textContent = newValue;
        }, 8000);
    }

    const placementElement = document.getElementById('developersPlaced');
    if (placementElement) {
        setInterval(() => {
            const currentValue = parseInt(placementElement.textContent) || 0;
            const newValue = currentValue + Math.floor(Math.random() * 2);
            placementElement.textContent = newValue + '';
        }, 12000);
    }

    const logElement = document.getElementById('healingLog');
    if (logElement) {
        setInterval(() => {
            const timestamp = new Date().toLocaleTimeString();
            const messages = [
                `[${timestamp}] System health check completed. All systems nominal.`,
                `[${timestamp}] Optimizing neural network parameters...`,
                `[${timestamp}] Updating SARS regulation database...`,
                `[${timestamp}] Processing GDELT data streams...`,
                `[${timestamp}] Validating developer skill assessments...`
            ];

            const randomMessage = messages[Math.floor(Math.random() * messages.length)];
            logElement.innerHTML = `<div>${randomMessage}</div>` + logElement.innerHTML;

            // Keep only last 4 messages
            const lines = logElement.innerHTML.split('</div>');
            if (lines.length > 4) {
                logElement.innerHTML = lines.slice(0, 4).join('</div>');
            }
        }, 15000);
    }
}

// Model highlighting functionality
function highlightModel(model) {
    document.querySelectorAll('.card-hover').forEach(card => {
        card.classList.remove('border-blue-500');
    });
    event.currentTarget.classList.add('border-blue-500');
}

// Engine toggle functionality
function toggleEngine(engine) {
    const engines = {
        financial: { status: 'financialStatus', active: 'Active', inactive: 'Standby' },
        guardian: { status: 'guardianStatus', active: 'Processing', inactive: 'Monitoring' },
        talent: { status: 'talentStatus', active: 'Active', inactive: 'Idle' }
    };

    const engineConfig = engines[engine];
    const statusElement = document.getElementById(engineConfig.status);

    if (statusElement) {
        const isActive = statusElement.textContent === engineConfig.active;
        statusElement.textContent = isActive ? engineConfig.inactive : engineConfig.active;

        // Visual feedback
        const button = event.currentTarget;
        button.style.transform = 'scale(0.95)';
        setTimeout(() => button.style.transform = 'scale(1)', 150);
    }
}

// Initialize scroll animations
function initializeAnimations() {
    if (typeof anime === 'undefined') return;

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

    document.querySelectorAll('.card-hover, section > div, .legal-section, .regulation-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

// Navigation functions
function scrollToDemo() {
    const el = document.getElementById('dashboard');
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Modal functions
function showEarlyAccess() {
    const modal = document.getElementById('earlyAccessModal');
    if (!modal) return;

    modal.classList.remove('hidden');
    modal.classList.add('flex');

    if (typeof anime !== 'undefined') {
        anime({
            targets: modal.querySelector('div'),
            scale: [0.8, 1],
            opacity: [0, 1],
            duration: 300,
            easing: 'easeOutCubic'
        });
    }
}

function hideEarlyAccess() {
    const modal = document.getElementById('earlyAccessModal');
    if (!modal) return;

    if (typeof anime !== 'undefined') {
        anime({
            targets: modal.querySelector('div'),
            scale: [1, 0.8],
            opacity: [1, 0],
            duration: 200,
            easing: 'easeInCubic',
            complete: () => {
                modal.classList.add('hidden');
                modal.classList.remove('flex');
            }
        });
    } else {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

// Use your custom submission logic
async function submitEarlyAccess(event) {
    event.preventDefault();
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerText;

    // 1. Get Data
    const formData = {
        email: form.querySelector('input[type="email"]').value,
        company: form.querySelector('input[type="text"]').value,
        industry: form.querySelector('select').value,
        source: 'vaal_uprising_landing_page'
    };

    // 2. Show Loading State
    submitBtn.innerText = "Processing...";
    submitBtn.disabled = true;

    try {
        // 3. Send to Backend
        const response = await fetch('/api/join-empire', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (!response.ok) throw new Error('Network response was not ok');

        // 4. Success Animation
        const modal = document.getElementById('earlyAccessModal');
        const content = modal.querySelector('div');

        content.innerHTML = `
            <div class="text-center">
                <div class="text-6xl mb-4">🚀</div>
                <h3 class="text-2xl font-bold text-white mb-4">Welcome to the Empire</h3>
                <p class="text-gray-300 mb-6">
                    You have been added to the Council. Check your email for the manifesto.
                </p>
                <button onclick="hideEarlyAccess()" class="btn-primary px-8 py-3 rounded-lg text-white font-semibold">
                    Return to Dashboard
                </button>
            </div>
        `;

        // Close after delay
        setTimeout(() => hideEarlyAccess(), 4000);

    } catch (error) {
        console.error('Error:', error);
        submitBtn.innerText = "Error - Try Again";
        submitBtn.disabled = false;
        setTimeout(() => submitBtn.innerText = originalText, 2000);
    }
}

// Payment System Integration
function initializePaymentSystem() {
    if (document.getElementById('paymentForm')) {
        initializePaymentForm();
    }
    initializePaymentTracking();
}

function initializePaymentForm() {
    const paymentForm = document.getElementById('paymentForm');
    if (!paymentForm) return;

    const paymentMethodSelect = paymentForm.querySelector('select');
    const cardElement = document.getElementById('cardElement');

    if (paymentMethodSelect && cardElement) {
        paymentMethodSelect.addEventListener('change', function() {
            if (this.value === 'card') {
                cardElement.classList.remove('hidden');
            } else {
                cardElement.classList.add('hidden');
            }
        });
    }
}
