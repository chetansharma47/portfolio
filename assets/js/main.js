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
  <span class="cli-highlight">bucket</span>     - Skills & future goals bucket / roadmap
  <span class="cli-highlight">ads</span>        - Advertisement board slots (TO-LET status)
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

        case 'bucket':
        case 'goals':
            {
                const lines = bucketItems.map(i => {
                    const st = bucketStatus(i);
                    const bar = '█'.repeat(Math.round(i.progress / 10)) + '░'.repeat(10 - Math.round(i.progress / 10));
                    return `  [${i.type === 'skill' ? 'SKILL' : ' GOAL'}] ${bar} ${String(i.progress).padStart(3)}%  ${i.title} <span class="cli-highlight">(${st.label} · ${i.target})</span>`;
                });
                printCliLine(`Bucket — Skills & Future Goals:\n${lines.join('\n')}\n\nScroll to the <span class="cli-cmd">Bucket &amp; Roadmap</span> section to add your own entries.`);
                document.getElementById('bucket').scrollIntoView({ behavior: 'smooth' });
            }
            break;

        case 'ads':
        case 'advertise':
            {
                const lines = AD_SLOTS.map(s => `  ${s.status === 'vacant' ? '<span class="cli-error">[TO-LET]</span>' : '<span class="cli-highlight">[BOOKED]</span>'} ${s.name} — ${s.size} | ${s.reach}`);
                printCliLine(`Advertisement Board — brand slots:\n${lines.join('\n')}\n\nAll vacant panels are open for booking. Mail <span class="cli-highlight">chetansharmap7@gmail.com</span> or hit "Book This Slot" on the board.`);
                document.getElementById('adboard').scrollIntoView({ behavior: 'smooth' });
            }
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

/* ============================================================
   BUCKET MODULE — Skills & Future Goals Roadmap
   Persisted in localStorage so entries survive reloads.
   ============================================================ */

const BUCKET_KEY = 'portfolio-bucket-v1';

const DEFAULT_BUCKET = [
    { id: 'b1', type: 'skill', title: 'Kubernetes CKA Certification', target: 'Q1 2027', note: 'Own cluster-level deployments end-to-end, not just Docker images.', progress: 35 },
    { id: 'b2', type: 'skill', title: 'Spring AI + RAG in Production', target: 'Q4 2026', note: 'Ship a real enterprise RAG service on a vector DB with Java 21.', progress: 60 },
    { id: 'b3', type: 'skill', title: 'AWS Solutions Architect — Associate', target: 'Q2 2027', note: 'Formalise the AWS work already done on Lambda, SES and Cognito.', progress: 20 },
    { id: 'b4', type: 'skill', title: 'Kafka Streams & Event-Driven Design', target: 'Q3 2026', note: 'Move from request/response thinking to streaming-first architecture.', progress: 45 },
    { id: 'b5', type: 'skill', title: 'Distributed System Design at Scale', target: 'Ongoing', note: 'HLD / LLD for multi-region, million-user systems.', progress: 55 },
    { id: 'b6', type: 'goal', title: 'Grow into a Lead / Architect Role', target: '2027', note: 'Own architecture decisions and mentor a full engineering pod.', progress: 40 },
    { id: 'b7', type: 'goal', title: 'Launch My Own SaaS Product', target: '2027', note: 'One product, real paying users, built and operated solo.', progress: 15 },
    { id: 'b8', type: 'goal', title: 'Speak at a Java / AI Tech Conference', target: '2027', note: 'Talk on bridging classic Java backends with AI agents.', progress: 10 },
    { id: 'b9', type: 'goal', title: 'Meaningful Open Source Contribution', target: 'Q4 2026', note: 'Merged PRs into a Spring / LangChain4j ecosystem project.', progress: 25 },
    { id: 'b10', type: 'goal', title: 'Work With a Global Distributed Team', target: 'Achieved', note: 'Weekly US client ownership on healthcare and travel-tech platforms.', progress: 100 }
];

let bucketItems = loadBucket();
let bucketFilter = 'all';

function loadBucket() {
    try {
        const raw = localStorage.getItem(BUCKET_KEY);
        if (!raw) return DEFAULT_BUCKET.slice();
        const parsed = JSON.parse(raw);
        return Array.isArray(parsed) && parsed.length ? parsed : DEFAULT_BUCKET.slice();
    } catch (e) {
        return DEFAULT_BUCKET.slice();
    }
}

function saveBucket() {
    try {
        localStorage.setItem(BUCKET_KEY, JSON.stringify(bucketItems));
    } catch (e) {
        showToast('Storage full — bucket could not be saved');
    }
}

function bucketStatus(item) {
    if (item.progress >= 100) return { key: 'done', label: 'Achieved' };
    if (item.progress > 0) return { key: 'progress', label: 'In Progress' };
    return { key: 'planned', label: 'Planned' };
}

function matchesBucketFilter(item) {
    if (bucketFilter === 'all') return true;
    if (bucketFilter === 'skill' || bucketFilter === 'goal') return item.type === bucketFilter;
    return bucketStatus(item).key === bucketFilter;
}

function escapeHtml(str) {
    return String(str === undefined || str === null ? '' : str).replace(/[&<>"']/g, function (c) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
}

function renderBucket() {
    const grid = document.getElementById('bucket-grid');
    const stats = document.getElementById('bucket-stats');
    if (!grid) return;

    const total = bucketItems.length;
    const done = bucketItems.filter(i => bucketStatus(i).key === 'done').length;
    const active = bucketItems.filter(i => bucketStatus(i).key === 'progress').length;
    const avg = total ? Math.round(bucketItems.reduce((s, i) => s + Number(i.progress || 0), 0) / total) : 0;

    if (stats) {
        stats.innerHTML =
            '<div class="bucket-stat"><span class="bucket-stat-num">' + total + '</span><span class="bucket-stat-label">In the Bucket</span></div>' +
            '<div class="bucket-stat"><span class="bucket-stat-num">' + active + '</span><span class="bucket-stat-label">In Progress</span></div>' +
            '<div class="bucket-stat"><span class="bucket-stat-num">' + done + '</span><span class="bucket-stat-label">Achieved</span></div>' +
            '<div class="bucket-stat"><span class="bucket-stat-num">' + avg + '%</span><span class="bucket-stat-label">Overall Completion</span></div>';
    }

    const visible = bucketItems.filter(matchesBucketFilter);

    if (!visible.length) {
        grid.innerHTML = '<div class="bucket-empty">Nothing in this view yet. Add the next skill or goal to the bucket.</div>';
        return;
    }

    grid.innerHTML = visible.map(function (item) {
        const st = bucketStatus(item);
        return '' +
            '<div class="bucket-card ' + item.type + '" data-id="' + escapeHtml(item.id) + '">' +
                '<div class="bucket-card-top">' +
                    '<span class="bucket-tag ' + item.type + '">' + (item.type === 'skill' ? 'Skill' : 'Goal') + '</span>' +
                    '<span class="bucket-status ' + st.key + '">' + st.label + '</span>' +
                '</div>' +
                '<h3 class="bucket-card-title">' + escapeHtml(item.title) + '</h3>' +
                (item.note ? '<p class="bucket-card-note">' + escapeHtml(item.note) + '</p>' : '') +
                '<div class="bucket-meta">' +
                    '<span class="bucket-target">Target: ' + escapeHtml(item.target || 'TBD') + '</span>' +
                    '<span class="bucket-percent">' + item.progress + '%</span>' +
                '</div>' +
                '<div class="bucket-bar"><div class="bucket-bar-fill" style="width:' + item.progress + '%"></div></div>' +
                '<div class="bucket-card-actions">' +
                    '<button class="bucket-mini" data-act="dec" title="Decrease progress">&minus;10%</button>' +
                    '<button class="bucket-mini" data-act="inc" title="Increase progress">+10%</button>' +
                    '<button class="bucket-mini" data-act="done" title="Mark as achieved">Mark Done</button>' +
                    '<button class="bucket-mini danger" data-act="del" title="Remove from bucket">Remove</button>' +
                '</div>' +
            '</div>';
    }).join('');
}

const bucketGrid = document.getElementById('bucket-grid');
if (bucketGrid) {
    bucketGrid.addEventListener('click', (e) => {
        const btn = e.target.closest('.bucket-mini');
        if (!btn) return;
        const card = btn.closest('.bucket-card');
        const item = bucketItems.find(i => i.id === card.dataset.id);
        if (!item) return;

        const act = btn.dataset.act;
        if (act === 'inc') item.progress = Math.min(100, Number(item.progress) + 10);
        else if (act === 'dec') item.progress = Math.max(0, Number(item.progress) - 10);
        else if (act === 'done') item.progress = 100;
        else if (act === 'del') {
            bucketItems = bucketItems.filter(i => i.id !== item.id);
            showToast('Removed from bucket');
        }

        if (act === 'done') showToast('Achieved: ' + item.title);
        saveBucket();
        renderBucket();
    });
}

const bucketFiltersBox = document.getElementById('bucket-filters');
if (bucketFiltersBox) {
    bucketFiltersBox.addEventListener('click', (e) => {
        const btn = e.target.closest('.bucket-filter');
        if (!btn) return;
        bucketFiltersBox.querySelectorAll('.bucket-filter').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        bucketFilter = btn.dataset.filter;
        renderBucket();
    });
}

const bucketForm = document.getElementById('bucket-form');
const bucketAddBtn = document.getElementById('bucket-add-btn');
const bucketCancelBtn = document.getElementById('bucket-cancel-btn');
const bucketProgressInput = document.getElementById('bucket-progress');

function toggleBucketForm(open) {
    if (!bucketForm) return;
    bucketForm.hidden = !open;
    bucketForm.classList.toggle('open', open);
    if (open) document.getElementById('bucket-title').focus();
}

if (bucketAddBtn) bucketAddBtn.addEventListener('click', () => toggleBucketForm(bucketForm.hidden));
if (bucketCancelBtn) bucketCancelBtn.addEventListener('click', () => { bucketForm.reset(); toggleBucketForm(false); });

if (bucketProgressInput) {
    bucketProgressInput.addEventListener('input', () => {
        document.getElementById('bucket-progress-val').textContent = bucketProgressInput.value + '%';
    });
}

if (bucketForm) {
    bucketForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const title = document.getElementById('bucket-title').value.trim();
        if (!title) return;

        bucketItems.unshift({
            id: 'b' + Date.now(),
            type: document.getElementById('bucket-type').value,
            title: title,
            target: document.getElementById('bucket-target').value.trim() || 'TBD',
            note: document.getElementById('bucket-note').value.trim(),
            progress: Number(bucketProgressInput.value)
        });

        saveBucket();
        renderBucket();
        bucketForm.reset();
        document.getElementById('bucket-progress-val').textContent = '0%';
        toggleBucketForm(false);
        showToast('Added to the bucket');
    });
}

const bucketExportBtn = document.getElementById('bucket-export-btn');
if (bucketExportBtn) {
    bucketExportBtn.addEventListener('click', () => {
        copyToClipboard(JSON.stringify(bucketItems, null, 2), 'Bucket JSON copied. Paste it into DEFAULT_BUCKET in main.js to publish it.');
    });
}

const bucketResetBtn = document.getElementById('bucket-reset-btn');
if (bucketResetBtn) {
    bucketResetBtn.addEventListener('click', () => {
        if (!confirm('Reset the bucket to the default list? Anything you added locally will be lost.')) return;
        bucketItems = DEFAULT_BUCKET.slice();
        saveBucket();
        renderBucket();
        showToast('Bucket reset to defaults');
    });
}

renderBucket();


/* ============================================================
   ADVERTISEMENT BOARD — Brand slots, currently TO-LET
   To fill a slot: set status to 'booked' and add
   brand / tagline / link / logo on that slot object.
   ============================================================ */

const AD_SLOTS = [
    {
        id: 'prime-billboard',
        name: 'Prime Billboard',
        size: '970 x 250 — Full Width',
        placement: 'Top panel, full width across the board',
        reach: 'Highest visibility on the page',
        status: 'vacant',
        tier: 'premium'
    },
    {
        id: 'panel-a',
        name: 'Panel A',
        size: '468 x 200 — Half Width',
        placement: 'Left board panel, upper row',
        reach: 'Recruiters and engineering leads',
        status: 'vacant'
    },
    {
        id: 'panel-b',
        name: 'Panel B',
        size: '468 x 200 — Half Width',
        placement: 'Right board panel, upper row',
        reach: 'Dev-tool and SaaS audience',
        status: 'vacant'
    },
    {
        id: 'strip-c',
        name: 'Strip C',
        size: '320 x 140 — Compact',
        placement: 'Lower board strip, left',
        reach: 'Startups and local businesses',
        status: 'vacant'
    },
    {
        id: 'strip-d',
        name: 'Strip D',
        size: '320 x 140 — Compact',
        placement: 'Lower board strip, centre',
        reach: 'Bootcamps, courses and communities',
        status: 'vacant'
    },
    {
        id: 'strip-e',
        name: 'Strip E',
        size: '320 x 140 — Compact',
        placement: 'Lower board strip, right',
        reach: 'Agencies and freelance networks',
        status: 'vacant'
    }
];

function renderAdBoard() {
    const grid = document.getElementById('ad-grid');
    if (!grid) return;

    grid.innerHTML = AD_SLOTS.map(function (slot) {
        if (slot.status === 'booked') {
            return '' +
                '<div class="ad-slot booked ' + (slot.tier || '') + '">' +
                    '<span class="ad-slot-code">' + escapeHtml(slot.name) + ' &middot; ' + escapeHtml(slot.size) + '</span>' +
                    '<div class="ad-creative">' +
                        (slot.logo ? '<img src="' + escapeHtml(slot.logo) + '" alt="' + escapeHtml(slot.brand) + '" class="ad-logo">' : '') +
                        '<h3 class="ad-brand">' + escapeHtml(slot.brand) + '</h3>' +
                        '<p class="ad-tagline">' + escapeHtml(slot.tagline) + '</p>' +
                        (slot.link ? '<a href="' + escapeHtml(slot.link) + '" target="_blank" rel="noopener sponsored" class="project-btn">Visit &#8599;</a>' : '') +
                    '</div>' +
                    '<span class="ad-booked-stamp">BOOKED</span>' +
                '</div>';
        }
        return '' +
            '<div class="ad-slot vacant ' + (slot.tier || '') + '" data-slot="' + escapeHtml(slot.id) + '">' +
                '<span class="ad-slot-code">' + escapeHtml(slot.name) + ' &middot; ' + escapeHtml(slot.size) + '</span>' +
                '<div class="tolet-stamp">TO-LET</div>' +
                '<h3 class="ad-vacant-title">YOUR AD HERE</h3>' +
                '<p class="ad-vacant-desc">' + escapeHtml(slot.placement) + '</p>' +
                '<p class="ad-vacant-reach">' + escapeHtml(slot.reach) + '</p>' +
                '<button class="bucket-btn primary ad-book-btn" data-slot="' + escapeHtml(slot.id) + '">Book This Slot</button>' +
                '<span class="ad-torn-strips"><i></i><i></i><i></i><i></i><i></i><i></i></span>' +
            '</div>';
    }).join('');
}

const adGrid = document.getElementById('ad-grid');
if (adGrid) {
    adGrid.addEventListener('click', (e) => {
        const btn = e.target.closest('.ad-book-btn');
        if (btn) openAdBooking(btn.dataset.slot);
    });
}

const adModal = document.getElementById('ad-modal');
const adModalClose = document.getElementById('ad-modal-close');
let activeAdSlot = null;

function openAdBooking(slotId) {
    if (!adModal) return;
    activeAdSlot = AD_SLOTS.find(s => s.id === slotId) || {
        id: 'exclusive',
        name: 'Exclusive Board Sponsorship',
        size: 'Every panel on the board',
        placement: 'Every panel on the board, single brand',
        reach: 'All portfolio traffic'
    };

    const box = document.getElementById('ad-modal-slot');
    if (box) {
        box.innerHTML =
            '<span class="ad-modal-code">' + escapeHtml(activeAdSlot.name) + '</span>' +
            '<p><b>Size:</b> ' + escapeHtml(activeAdSlot.size) + '</p>' +
            '<p><b>Placement:</b> ' + escapeHtml(activeAdSlot.placement) + '</p>' +
            '<p><b>Audience:</b> ' + escapeHtml(activeAdSlot.reach) + '</p>' +
            '<p class="ad-modal-hint">Rates are negotiated per campaign. Share the budget you have in mind and I will reply with availability, creative specs and terms.</p>';
    }

    adModal.classList.add('open');
    trackEvent('ad_booking_opened', { slot: activeAdSlot.name });
    const brandInput = document.getElementById('ad-brand');
    if (brandInput) brandInput.focus();
}

function closeAdBooking() {
    if (adModal) adModal.classList.remove('open');
}

if (adModalClose) adModalClose.addEventListener('click', closeAdBooking);
if (adModal) {
    adModal.addEventListener('click', (e) => { if (e.target === adModal) closeAdBooking(); });
}

document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    closeAdBooking();
    if (cliModal) cliModal.classList.remove('open');
});

/* Enquiries post to the site's own serverless endpoint (api/enquiry.js),
   which sends the mail through the Resend API. Nothing is routed through a
   third-party form relay, and the API key never reaches the browser. */
const OWNER_EMAIL = 'chetansharmap7@gmail.com';
const ENQUIRY_ENDPOINT = '/api/enquiry';

const adForm = document.getElementById('ad-form');
const adSubmitBtn = document.getElementById('ad-submit');
const adStatusBox = document.getElementById('ad-form-status');

/* Vercel Analytics custom event, ignored when analytics is unavailable. */
function trackEvent(name, props) {
    if (typeof window.vercelTrack !== 'function') return;
    try {
        window.vercelTrack(name, props);
    } catch (err) {
        /* analytics must never break a submission */
    }
}

function setEnquiryStatus(text, state) {
    if (!adStatusBox) return;
    adStatusBox.textContent = text;
    adStatusBox.className = 'ad-form-status' + (state ? ' ' + state : '');
}

function buildEnquiryText(data) {
    return [
        'Brand / Company: ' + data.brand,
        'Contact Email: ' + data.email,
        'Budget Offer: ' + data.budget + ' ' + data.currency + ' (' + data.cycle + ')',
        'Slot Requested: ' + data.slotName + ' (' + data.slotSize + ')',
        'Placement: ' + data.placement,
        '',
        'Message: ' + data.message
    ].join('\n');
}

if (adForm) {
    adForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const slot = activeAdSlot || {};
        const data = {
            brand: document.getElementById('ad-brand').value.trim(),
            email: document.getElementById('ad-email').value.trim(),
            budget: document.getElementById('ad-budget').value.trim(),
            currency: document.getElementById('ad-currency').value,
            cycle: document.getElementById('ad-cycle').value,
            message: document.getElementById('ad-message').value.trim(),
            slotName: slot.name || 'Portfolio Board',
            slotSize: slot.size || 'N/A',
            placement: slot.placement || 'N/A'
        };

        if (!data.brand || !data.email || !data.budget || !data.message) {
            setEnquiryStatus('Brand, email, budget and message are all required.', 'error');
            return;
        }

        const subject = 'Ad Slot Enquiry: ' + data.slotName + ' — ' + data.brand +
            ' (' + data.budget + ' ' + data.currency + ' ' + data.cycle.toLowerCase() + ')';

        const mailtoFallback = 'mailto:' + OWNER_EMAIL + '?subject=' + encodeURIComponent(subject) +
            '&body=' + encodeURIComponent(buildEnquiryText(data));

        /* The send endpoint only exists on the deployed site, so a copy opened
           straight off disk hands the enquiry to the mail app instead. */
        if (window.location.protocol === 'file:') {
            setEnquiryStatus('Direct send needs the published site, not a local file copy. Opening your mail app with the same details.', 'error');
            window.location.href = mailtoFallback;
            return;
        }

        if (adSubmitBtn) {
            adSubmitBtn.disabled = true;
            adSubmitBtn.textContent = 'Sending...';
        }
        setEnquiryStatus('Sending your enquiry...', 'pending');

        fetch(ENQUIRY_ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
            body: JSON.stringify({
                brand: data.brand,
                email: data.email,
                budget: data.budget,
                currency: data.currency,
                cycle: data.cycle,
                message: data.message,
                slotName: data.slotName,
                slotSize: data.slotSize,
                placement: data.placement
            })
        })
            .then(function (res) {
                return res.json().catch(function () { return {}; }).then(function (body) {
                    if (!res.ok || body.ok !== true) {
                        throw new Error(body.error || ('Request failed (' + res.status + ')'));
                    }
                    return body;
                });
            })
            .then(function () {
                setEnquiryStatus('Enquiry sent. You will get a reply within 24 hours.', 'success');
                showToast('Enquiry sent to Chetan Sharma');
                trackEvent('ad_enquiry_sent', {
                    slot: data.slotName,
                    currency: data.currency,
                    cycle: data.cycle
                });
                adForm.reset();
                setTimeout(function () {
                    closeAdBooking();
                    setEnquiryStatus('', '');
                }, 2200);
            })
            .catch(function (err) {
                const reason = (err && err.message) ? err.message : 'network error';
                console.error('Ad enquiry direct send failed:', reason);

                if (/not configured/i.test(reason)) {
                    setEnquiryStatus('The mail service is not configured on the server yet. Opening your mail app so this enquiry still reaches him.', 'error');
                } else {
                    setEnquiryStatus('Could not send directly (' + reason + '). Opening your mail app with the same details.', 'error');
                }

                window.location.href = mailtoFallback;
            })
            .then(function () {
                if (adSubmitBtn) {
                    adSubmitBtn.disabled = false;
                    adSubmitBtn.textContent = 'Send Enquiry';
                }
            });
    });
}

renderAdBoard();
