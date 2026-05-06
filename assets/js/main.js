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
    particleColor: 'rgba(0, 240, 255, 0.6)',
    particleRadius: 2,
    particleCount: 200,
    particleMaxVelocity: 0.5,
    lineLength: 180,
    cursorRadius: 120,
    particleLife: 6
};

window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
});

window.addEventListener('mousemove', (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY + window.scrollY;
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
            const scrollY = window.scrollY;
            const dx = mouse.x - this.x;
            const dy = (mouse.y - scrollY) - this.y;
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
    const cy = mouse.y - window.scrollY;
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
    const cy = mouse.y !== null ? mouse.y - window.scrollY : null;
    for (let i in particles) {
        if (cy !== null) {
            const dx = particles[i].x - mouse.x;
            const dy = particles[i].y - cy;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < properties.cursorRadius) {
                opacity = (1 - dist / properties.cursorRadius) * 0.8;
                ctx.lineWidth = 0.8;
                ctx.strokeStyle = `rgba(0, 240, 255, ${opacity})`;
                ctx.beginPath();
                ctx.moveTo(mouse.x, cy);
                ctx.lineTo(particles[i].x, particles[i].y);
                ctx.stroke();
            }
        }
        for (let j in particles) {
            x1 = particles[i].x; y1 = particles[i].y;
            x2 = particles[j].x; y2 = particles[j].y;
            length = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
            if (length < properties.lineLength) {
                opacity = 1 - length / properties.lineLength;
                ctx.lineWidth = '0.5';
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
