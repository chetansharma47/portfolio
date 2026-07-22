const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
}, { threshold: 0.1 });

document.querySelectorAll('.fade-up').forEach((el) => observer.observe(el));

const canvas = document.getElementById('neural-canvas');
const ctx = canvas.getContext('2d');

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

let particles = [];
let mouse = { x: null, y: null };
const properties = {
    bgColor: '#000',
    particleColor: 'rgba(0, 240, 255, 0.45)',
    particleRadius: 1.5,
    particleCount: 90,
    particleMaxVelocity: 0.35,
    lineLength: 160,
    cursorRadius: 110,
    particleLife: 6
};

window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
});

window.addEventListener('mousemove', (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;

    const octWrapper = document.querySelector('.octopus-wrapper');
    const gridLayer = document.querySelector('.cyber-grid-layer');
    const moveX = (e.clientX - window.innerWidth / 2) * 0.015;
    const moveY = (e.clientY - window.innerHeight / 2) * 0.015;

    if (octWrapper) octWrapper.style.transform = `translate3d(${moveX}px, ${moveY}px, 0)`;
    if (gridLayer) gridLayer.style.transform = `translate3d(${moveX * 0.6}px, ${moveY * 0.6}px, 0)`;
});
window.addEventListener('mouseleave', () => { mouse.x = null; mouse.y = null; });

class Particle {
    constructor() {
        this.reset();
    }
    reset() {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.velocityX = Math.random() * (properties.particleMaxVelocity * 2) - properties.particleMaxVelocity;
        this.velocityY = Math.random() * (properties.particleMaxVelocity * 2) - properties.particleMaxVelocity;
        this.life = Math.random() * properties.particleLife * 60;
    }
    position() {
        if (mouse.x !== null) {
            const dx = mouse.x - this.x;
            const dy = mouse.y - this.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < properties.cursorRadius && dist > 1) {
                const force = (properties.cursorRadius - dist) / properties.cursorRadius;
                this.velocityX += (dx / dist) * force * 0.3;
                this.velocityY += (dy / dist) * force * 0.3;
                const speed = Math.sqrt(this.velocityX ** 2 + this.velocityY ** 2);
                if (speed > 3) {
                    this.velocityX = (this.velocityX / speed) * 3;
                    this.velocityY = (this.velocityY / speed) * 3;
                }
            } else {
                this.velocityX *= 0.98;
                this.velocityY *= 0.98;
            }
        }
        if (this.x + this.velocityX > canvas.width || this.x + this.velocityX < 0) this.velocityX *= -1;
        if (this.y + this.velocityY > canvas.height || this.y + this.velocityY < 0) this.velocityY *= -1;
        this.x += this.velocityX;
        this.y += this.velocityY;
    }
    reDraw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, properties.particleRadius, 0, Math.PI * 2);
        ctx.closePath();
        ctx.fillStyle = properties.particleColor;
        ctx.fill();
    }
}

function reDrawBackground() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

function drawCursorGlow() {
    if (mouse.x === null) return;
    const cy = mouse.y;
    const grad = ctx.createRadialGradient(mouse.x, cy, 0, mouse.x, cy, 60);
    grad.addColorStop(0, 'rgba(0, 240, 255, 0.18)');
    grad.addColorStop(0.5, 'rgba(138, 43, 226, 0.08)');
    grad.addColorStop(1, 'rgba(0, 240, 255, 0)');
    ctx.beginPath();
    ctx.arc(mouse.x, cy, 60, 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.fill();
    ctx.beginPath();
    ctx.arc(mouse.x, cy, 3, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(0, 240, 255, 0.95)';
    ctx.shadowBlur = 12;
    ctx.shadowColor = '#00f0ff';
    ctx.fill();
    ctx.shadowBlur = 0;
}

function drawLines() {
    let x1, y1, x2, y2, length, opacity;
    const cy = mouse.y;
    const count = particles.length;
    for (let i = 0; i < count; i++) {
        const p1 = particles[i];
        if (cy !== null) {
            const dx = p1.x - mouse.x;
            const dy = p1.y - cy;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < properties.cursorRadius) {
                opacity = (1 - dist / properties.cursorRadius) * 0.8;
                ctx.lineWidth = 0.8;
                ctx.strokeStyle = `rgba(0, 240, 255, ${opacity})`;
                ctx.beginPath();
                ctx.moveTo(mouse.x, cy);
                ctx.lineTo(p1.x, p1.y);
                ctx.stroke();
            }
        }
        for (let j = i + 1; j < count; j++) {
            const p2 = particles[j];
            x1 = p1.x; y1 = p1.y;
            x2 = p2.x; y2 = p2.y;
            length = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
            if (length < properties.lineLength) {
                opacity = 1 - length / properties.lineLength;
                ctx.lineWidth = 0.5;
                ctx.strokeStyle = `rgba(138, 43, 226, ${opacity * 0.8})`;
                ctx.beginPath();
                ctx.moveTo(x1, y1);
                ctx.lineTo(x2, y2);
                ctx.closePath();
                ctx.stroke();
            }
        }
    }
}

function reDrawParticles() {
    for (let i in particles) {
        particles[i].position();
        particles[i].reDraw();
    }
}

function loop() {
    reDrawBackground();
    drawCursorGlow();
    reDrawParticles();
    drawLines();
    requestAnimationFrame(loop);
}

function init() {
    for (let i = 0; i < properties.particleCount; i++) {
        particles.push(new Particle);
    }
    loop();
}

init();

function showSkill(btn, title, details) {
    const node = btn.closest('.skill-node');
    node.querySelectorAll('.interactive-pill').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    let detailBox = node.querySelector('.skill-detail-box');
    if (!detailBox) {
        detailBox = document.createElement('div');
        detailBox.className = 'skill-detail-box';
        detailBox.innerHTML = '<h4 class="detail-title"></h4><ul class="skill-detail-list"></ul>';
        node.appendChild(detailBox);
    }
    detailBox.querySelector('.detail-title').textContent = title;
    const ul = detailBox.querySelector('.skill-detail-list');
    ul.innerHTML = '';
    details.forEach(item => {
        const li = document.createElement('li');
        li.textContent = item;
        ul.appendChild(li);
    });
    detailBox.style.display = 'block';
}

document.addEventListener('click', function (e) {
    if (!e.target.closest('.interactive-pill') && !e.target.closest('.skill-detail-box')) {
        document.querySelectorAll('.skill-detail-box').forEach(box => box.style.display = 'none');
        document.querySelectorAll('.interactive-pill').forEach(p => p.classList.remove('active'));
    }
});

// Active Navbar Link Scroll Highlight
const navObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const id = entry.target.getAttribute('id');
            document.querySelectorAll('.nav-links a').forEach(link => {
                if (link.getAttribute('href') === `#${id}`) {
                    link.classList.add('active');
                } else {
                    link.classList.remove('active');
                }
            });
        }
    });
}, { threshold: 0.3 });

document.querySelectorAll('section[id]').forEach(section => navObserver.observe(section));

// Copy to Clipboard HUD Toast
function copyToClipboard(text, message) {
    navigator.clipboard.writeText(text).then(() => {
        showToast(message || 'Copied to clipboard!');
    }).catch(() => {
        showToast('Failed to copy to clipboard');
    });
}

function showToast(message) {
    const toast = document.getElementById('hud-toast');
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Dark & Light Mode Theme Switcher
const themeToggleBtn = document.getElementById('theme-toggle');
const storedTheme = localStorage.getItem('portfolio-theme') || 'dark';

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    if (themeToggleBtn) {
        themeToggleBtn.textContent = theme === 'light' ? '🌙' : '☀️';
    }
    if (theme === 'light') {
        properties.particleColor = 'rgba(2, 132, 199, 0.6)';
    } else {
        properties.particleColor = 'rgba(0, 240, 255, 0.6)';
    }
    localStorage.setItem('portfolio-theme', theme);
}

applyTheme(storedTheme);

if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
        const activeTheme = document.documentElement.getAttribute('data-theme') || 'dark';
        applyTheme(activeTheme === 'dark' ? 'light' : 'dark');
    });
}

// Interactive CLI Console Modal
const cliTrigger = document.getElementById('cli-trigger');
const cliModal = document.getElementById('cli-modal');
const cliClose = document.getElementById('cli-close');
const cliInput = document.getElementById('cli-input');
const cliOutput = document.getElementById('cli-output');

if (cliTrigger && cliModal) {
    cliTrigger.addEventListener('click', () => {
        cliModal.classList.add('open');
        cliInput.focus();
    });
}

if (cliClose && cliModal) {
    cliClose.addEventListener('click', () => {
        cliModal.classList.remove('open');
    });
}

if (cliInput) {
    cliInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const cmd = cliInput.value.trim().toLowerCase();
            cliInput.value = '';
            handleCliCommand(cmd);
        }
    });
}

function printCliLine(text, isCmd = false) {
    const line = document.createElement('div');
    line.className = isCmd ? 'cli-line user-cmd' : 'cli-line';
    line.innerHTML = text;
    cliOutput.appendChild(line);
    cliOutput.scrollTop = cliOutput.scrollHeight;
}

function handleCliCommand(cmd) {
    if (!cmd) return;
    printCliLine(`<span class="cli-prompt">chetan@dev-system:~$</span> ${cmd}`, true);

    switch (cmd) {
        case 'help':
            printCliLine(`Available Commands:
  <span class="cli-highlight">about</span>      - Developer profile & architecture philosophy
  <span class="cli-highlight">experience</span> - Full execution history & enterprise roles
  <span class="cli-highlight">projects</span>   - Live production SaaS, US Healthcare & Travel-Tech
  <span class="cli-highlight">skills</span>     - Java 21, Spring Boot, Angular 20 & AWS tech stack
  <span class="cli-highlight">contact</span>    - Direct email & phone channels
  <span class="cli-highlight">hire</span>       - Why hire Chetan Sharma?
  <span class="cli-highlight">clear</span>      - Clear console screen
  <span class="cli-highlight">exit</span>       - Close console terminal`);
            break;

        case 'about':
        case 'bio':
            printCliLine(`Chetan Sharma — Full Stack Java Developer & AI Engineer
Based in Mohali, Punjab, India. End-to-end production owner specializing in high-throughput Java 21 backends, Angular 20 migrations, multi-DB architecture, and enterprise GenAI team leadership.`);
            break;

        case 'experience':
        case 'roles':
            printCliLine(`Enterprise Roles:
1. <span class="cli-highlight">Master Software Solutions</span> (Jan 2024 - Present): Full Stack Developer (WhiteLabel Platform)
   • Angular 20 migration (35-45% load boost) | Multi-DB (PostgreSQL, MySQL, MSSQL) | PostgreSQL 80% acceleration (2s -> 400ms)
2. <span class="cli-highlight">Illuminate Health, USA Client</span> (Oct 2022 - Jan 2024): Sr. Java Software Engineer
   • Cloud Healthcare Platform | AWS Serverless (~10K Lambda jobs/day) | Saved 100+ hrs/mo via Superset & UiPath ETL | Jitsi Video -> https://illuminate.health/
3. <span class="cli-highlight">ToXSL Technologies / Revelex, USA Client</span> (Jan 2022 - Sep 2022): Java Developer
   • US Travel-Tech Engine powering global airlines, hotels & cruise lines -> https://www.revelex.com/en`);
            break;

        case 'projects':
            printCliLine(`Featured Production Projects:
1. <span class="cli-highlight">WhiteLabel Enterprise Web Platform</span> (Java 21, Spring MVC, Angular 20, PostgreSQL/MySQL/MSSQL, iText, AspectJ)
2. <span class="cli-highlight">Illuminate Health Cloud & Automation Platform - USA Client</span> (AWS Lambda, SES, Cognito, Apache Superset, UiPath, Jitsi Video) -> https://illuminate.health/
3. <span class="cli-highlight">Revelex Global Travel Engine - USA Client</span> (Java, Spring Boot, REST APIs, MySQL) -> https://www.revelex.com/en
4. <span class="cli-highlight">Enterprise GenAI & AI Agent Task Force</span> (Claude API, Spring AI, LangChain4j, Prompt Engineering)`);
            break;

        case 'skills':
            printCliLine(`Tech Arsenal:
• Backend: Java 21, Java 8, Spring Boot 2.3/3.x, Spring MVC, Hibernate 5.6, AspectJ, iText PDF, Swagger, REST APIs
• Frontend: Angular 20, AngularJS (Migration Expert), TypeScript, HTML5, CSS3, Tailwind
• Databases: PostgreSQL (Query Optimization ~80%), MySQL, MSSQL
• Cloud & Tools: AWS (SES, Lambda ~10K jobs/day, Cognito), Apache Superset, KNIME, UiPath ETL, LDAP SSO, Jitsi Video
• AI & GenAI: Internal AI Team Member, Claude Setup, Prompt Engineering, Spring AI, LangChain4j`);
            break;

        case 'contact':
            printCliLine(`Email: chetansharmap7@gmail.com
Phone: +91 8708982388
Location: Mohali, Punjab, India
LinkedIn: https://linkedin.com/in/chetan-sharma-dev47`);
            break;

        case 'hire':
            printCliLine(`🚀 High-Impact Developer with Proven Results:
• Zero-downtime AngularJS -> Angular 20 frontend migration (35-45% initial load speedup)
• 80% PostgreSQL query latency reduction (2.0s -> 400ms)
• 100+ hours/month automated via Apache Superset & UiPath/KNIME ETL
• Internal AI Team Mentor guiding prompt engineering and GenAI integrations`);
            break;

        case 'clear':
            cliOutput.innerHTML = '<div class="cli-line sys-line">SYSTEM READY. Type <span class="cli-cmd">help</span> for available commands.</div>';
            break;

        case 'exit':
            cliModal.classList.remove('open');
            break;

        default:
            printCliLine(`Command not recognized: '<span class="cli-error">${cmd}</span>'. Type <span class="cli-cmd">help</span> for available commands.`);
            break;
    }
}

// Interactive 3D Card Tilt Effect
document.querySelectorAll('.project-card, .skill-node, .metric-card').forEach(card => {
    card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        const rotateX = ((y - centerY) / centerY) * -7;
        const rotateY = ((x - centerX) / centerX) * 7;
        card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-5px)`;
    });

    card.addEventListener('mouseleave', () => {
        card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0)`;
    });
});

// Scroll Metric Counter Animation
let metricsAnimated = false;
const metricsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting && !metricsAnimated) {
            metricsAnimated = true;
            animateMetricNumbers();
        }
    });
}, { threshold: 0.5 });

const metricsSec = document.getElementById('metrics');
if (metricsSec) metricsObserver.observe(metricsSec);

function animateMetricNumbers() {
    const metricCards = document.querySelectorAll('.metric-card');
    const targetValues = [3, 99.9, 100, 80];
    const prefixes = ['', '', '', '>'];
    const suffixes = ['+', '%', '+', '%'];

    metricCards.forEach((card, idx) => {
        const numElem = card.querySelector('.metric-number');
        if (!numElem) return;
        let start = 0;
        const target = targetValues[idx];
        const duration = 1800;
        const startTime = performance.now();

        function updateCounter(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const currentVal = target === 99.9
                ? (progress * 99.9).toFixed(1)
                : Math.floor(progress * target);

            numElem.textContent = `${prefixes[idx]}${currentVal}${suffixes[idx]}`;

            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            } else {
                numElem.textContent = `${prefixes[idx]}${target}${suffixes[idx]}`;
            }
        }
        requestAnimationFrame(updateCounter);
    });
}

// Mobile Navigation Menu Handler
const mobileMenuBtn = document.getElementById('mobile-menu-btn');
const navMenu = document.getElementById('nav-menu');

if (mobileMenuBtn && navMenu) {
    mobileMenuBtn.addEventListener('click', () => {
        mobileMenuBtn.classList.toggle('open');
        navMenu.classList.toggle('open');
    });

    document.querySelectorAll('.nav-links a').forEach(link => {
        link.addEventListener('click', () => {
            mobileMenuBtn.classList.remove('open');
            navMenu.classList.remove('open');
        });
    });
}
