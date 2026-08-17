/**
 * Public site behaviour for the server-rendered pages.
 *
 * All content is rendered by the server; this file only adds interaction:
 * theme, navigation, reveal animations, the particle background, skill
 * details, metric counters, bucket filtering, the ad booking modal and the
 * terminal console.
 */

const SITE = (() => {
    const node = document.getElementById('site-data');
    if (!node) return {};
    try {
        return JSON.parse(node.textContent || '{}');
    } catch (err) {
        return {};
    }
})();

/* ---------------------------------------------------------------- reveal */

const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
        if (entry.isIntersecting) entry.target.classList.add('visible');
    });
}, { threshold: 0.1 });

document.querySelectorAll('.fade-up').forEach((el) => revealObserver.observe(el));

const navObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const id = entry.target.getAttribute('id');
        document.querySelectorAll('.nav-links a').forEach((link) => {
            link.classList.toggle('active', link.getAttribute('href') === `#${id}`);
        });
    });
}, { threshold: 0.3 });

document.querySelectorAll('section[id]').forEach((section) => navObserver.observe(section));

/* ------------------------------------------------------------------ toast */

function showToast(message) {
    const toast = document.getElementById('hud-toast');
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

function copyToClipboard(text, message) {
    if (!text) return;
    navigator.clipboard.writeText(text)
        .then(() => showToast(message || 'Copied to clipboard'))
        .catch(() => showToast('Could not copy to clipboard'));
}

document.addEventListener('click', (e) => {
    const target = e.target.closest('[data-copy]');
    if (!target) return;
    copyToClipboard(target.dataset.copy, target.dataset.copyMessage);
});

/* ------------------------------------------------------------------ theme */

const themeToggleBtn = document.getElementById('theme-toggle');
const particleColours = { dark: 'rgba(0, 240, 255, 0.6)', light: 'rgba(2, 132, 199, 0.6)' };

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    if (themeToggleBtn) themeToggleBtn.textContent = theme === 'light' ? '☽' : '☀';
    properties.particleColor = particleColours[theme] || particleColours.dark;
    localStorage.setItem('portfolio-theme', theme);
}

if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
        const active = document.documentElement.getAttribute('data-theme') || 'dark';
        applyTheme(active === 'dark' ? 'light' : 'dark');
    });
}

/* -------------------------------------------------------- particle canvas */

const canvas = document.getElementById('neural-canvas');
const ctx = canvas ? canvas.getContext('2d') : null;
const properties = {
    particleColor: 'rgba(0, 240, 255, 0.45)',
    particleRadius: 1.5,
    particleCount: 90,
    particleMaxVelocity: 0.35,
    lineLength: 160,
    cursorRadius: 110
};

let particles = [];
let mouse = { x: null, y: null };

if (canvas && ctx) {
    const resize = () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    window.addEventListener('mousemove', (e) => {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
        const gridLayer = document.querySelector('.cyber-grid-layer');
        if (gridLayer) {
            const moveX = (e.clientX - window.innerWidth / 2) * 0.009;
            const moveY = (e.clientY - window.innerHeight / 2) * 0.009;
            gridLayer.style.transform = `translate3d(${moveX}px, ${moveY}px, 0)`;
        }
    });
    window.addEventListener('mouseleave', () => { mouse = { x: null, y: null }; });

    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.vx = Math.random() * properties.particleMaxVelocity * 2 - properties.particleMaxVelocity;
            this.vy = Math.random() * properties.particleMaxVelocity * 2 - properties.particleMaxVelocity;
        }
        step() {
            if (mouse.x !== null) {
                const dx = mouse.x - this.x;
                const dy = mouse.y - this.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < properties.cursorRadius && dist > 1) {
                    const force = (properties.cursorRadius - dist) / properties.cursorRadius;
                    this.vx += (dx / dist) * force * 0.3;
                    this.vy += (dy / dist) * force * 0.3;
                    const speed = Math.sqrt(this.vx ** 2 + this.vy ** 2);
                    if (speed > 3) {
                        this.vx = (this.vx / speed) * 3;
                        this.vy = (this.vy / speed) * 3;
                    }
                } else {
                    this.vx *= 0.98;
                    this.vy *= 0.98;
                }
            }
            if (this.x + this.vx > canvas.width || this.x + this.vx < 0) this.vx *= -1;
            if (this.y + this.vy > canvas.height || this.y + this.vy < 0) this.vy *= -1;
            this.x += this.vx;
            this.y += this.vy;
        }
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, properties.particleRadius, 0, Math.PI * 2);
            ctx.fillStyle = properties.particleColor;
            ctx.fill();
        }
    }

    function drawLines() {
        for (let i = 0; i < particles.length; i++) {
            const p1 = particles[i];
            if (mouse.x !== null) {
                const dist = Math.hypot(p1.x - mouse.x, p1.y - mouse.y);
                if (dist < properties.cursorRadius) {
                    ctx.lineWidth = 0.8;
                    ctx.strokeStyle = `rgba(0, 240, 255, ${(1 - dist / properties.cursorRadius) * 0.8})`;
                    ctx.beginPath();
                    ctx.moveTo(mouse.x, mouse.y);
                    ctx.lineTo(p1.x, p1.y);
                    ctx.stroke();
                }
            }
            for (let j = i + 1; j < particles.length; j++) {
                const p2 = particles[j];
                const length = Math.hypot(p2.x - p1.x, p2.y - p1.y);
                if (length < properties.lineLength) {
                    ctx.lineWidth = 0.5;
                    ctx.strokeStyle = `rgba(138, 43, 226, ${(1 - length / properties.lineLength) * 0.8})`;
                    ctx.beginPath();
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.stroke();
                }
            }
        }
    }

    function frame() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach((p) => { p.step(); p.draw(); });
        drawLines();
        requestAnimationFrame(frame);
    }

    for (let i = 0; i < properties.particleCount; i++) particles.push(new Particle());
    frame();
}

applyTheme(localStorage.getItem('portfolio-theme') || SITE.defaultTheme || 'dark');

/* ------------------------------------------------------------ mobile menu */

const mobileMenuBtn = document.getElementById('mobile-menu-btn');
const navMenu = document.getElementById('nav-menu');

if (mobileMenuBtn && navMenu) {
    mobileMenuBtn.addEventListener('click', () => {
        mobileMenuBtn.classList.toggle('open');
        navMenu.classList.toggle('open');
    });
    document.querySelectorAll('.nav-links a').forEach((link) => {
        link.addEventListener('click', () => {
            mobileMenuBtn.classList.remove('open');
            navMenu.classList.remove('open');
        });
    });
}

/* ----------------------------------------------------------- skill detail */

document.querySelectorAll('.interactive-pill').forEach((pill) => {
    pill.addEventListener('click', () => {
        const node = pill.closest('.skill-node');
        if (!node) return;
        node.querySelectorAll('.interactive-pill').forEach((p) => p.classList.remove('active'));
        pill.classList.add('active');

        let box = node.querySelector('.skill-detail-box');
        if (!box) {
            box = document.createElement('div');
            box.className = 'skill-detail-box';
            box.innerHTML = '<h4 class="detail-title"></h4><ul class="skill-detail-list"></ul>';
            node.appendChild(box);
        }
        box.querySelector('.detail-title').textContent = pill.dataset.skill || pill.textContent.trim();

        let details = [];
        try {
            details = JSON.parse(pill.dataset.details || '[]');
        } catch (err) {
            details = [];
        }
        const list = box.querySelector('.skill-detail-list');
        list.innerHTML = '';
        details.forEach((line) => {
            const li = document.createElement('li');
            li.textContent = line;
            list.appendChild(li);
        });
        box.style.display = 'block';
    });
});

document.addEventListener('click', (e) => {
    if (e.target.closest('.interactive-pill') || e.target.closest('.skill-detail-box')) return;
    document.querySelectorAll('.skill-detail-box').forEach((box) => { box.style.display = 'none'; });
    document.querySelectorAll('.interactive-pill').forEach((p) => p.classList.remove('active'));
});

/* --------------------------------------------------------- metric counters */

let metricsAnimated = false;
const metricsSection = document.getElementById('metrics');

if (metricsSection) {
    new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (!entry.isIntersecting || metricsAnimated) return;
            metricsAnimated = true;
            document.querySelectorAll('.metric-number').forEach((el) => {
                const target = parseFloat(el.dataset.target || '');
                if (!Number.isFinite(target)) return;
                const decimals = (el.dataset.target || '').includes('.') ? 1 : 0;
                const prefix = el.dataset.prefix || '';
                const suffix = el.dataset.suffix || '';
                const started = performance.now();
                const duration = 1600;

                const tick = (now) => {
                    const progress = Math.min((now - started) / duration, 1);
                    const value = (target * progress).toFixed(decimals);
                    el.textContent = `${prefix}${value}${suffix}`;
                    if (progress < 1) requestAnimationFrame(tick);
                };
                requestAnimationFrame(tick);
            });
        });
    }, { threshold: 0.5 }).observe(metricsSection);
}

/* ---------------------------------------------------------- card tilt fx */

document.querySelectorAll('.project-card, .skill-node, .metric-card').forEach((card) => {
    card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const rotateX = ((e.clientY - rect.top - rect.height / 2) / (rect.height / 2)) * -6;
        const rotateY = ((e.clientX - rect.left - rect.width / 2) / (rect.width / 2)) * 6;
        card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-5px)`;
    });
    card.addEventListener('mouseleave', () => {
        card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0)';
    });
});

/* ------------------------------------------------------- bucket filtering */

const bucketFilters = document.getElementById('bucket-filters');

if (bucketFilters) {
    bucketFilters.addEventListener('click', (e) => {
        const btn = e.target.closest('.bucket-filter');
        if (!btn) return;
        bucketFilters.querySelectorAll('.bucket-filter').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');

        const filter = btn.dataset.filter;
        document.querySelectorAll('#bucket-grid .bucket-card').forEach((card) => {
            const matches = filter === 'all'
                || card.dataset.type === filter
                || card.dataset.state === filter;
            card.style.display = matches ? '' : 'none';
        });
    });
}

/* ------------------------------------------------------------- analytics */

function trackEvent(name, props) {
    if (typeof window.vercelTrack !== 'function') return;
    try {
        window.vercelTrack(name, props);
    } catch (err) {
        /* analytics must never break the page */
    }
}

/* ------------------------------------------------------- ad booking modal */

const adModal = document.getElementById('ad-modal');
const adForm = document.getElementById('ad-form');
const adSubmitBtn = document.getElementById('ad-submit');
const adStatusBox = document.getElementById('ad-form-status');
const adSlotInput = document.getElementById('ad-slot-key');

function setEnquiryStatus(text, state) {
    if (!adStatusBox) return;
    adStatusBox.textContent = text;
    adStatusBox.className = 'ad-form-status' + (state ? ` ${state}` : '');
}

function openAdBooking(slotKey) {
    if (!adModal) return;
    const card = document.querySelector(`.ad-slot[data-slot="${slotKey}"]`);
    const slot = card
        ? {
            key: slotKey,
            name: card.dataset.name,
            size: card.dataset.size,
            placement: card.dataset.placement,
            reach: card.dataset.reach
        }
        : {
            key: 'exclusive',
            name: 'Exclusive Board Sponsorship',
            size: 'Every panel on the board',
            placement: 'Full board takeover, single brand',
            reach: 'All portfolio traffic'
        };

    if (adSlotInput) adSlotInput.value = card ? slotKey : '';
    const box = document.getElementById('ad-modal-slot');
    if (box) {
        box.innerHTML = '';
        const title = document.createElement('span');
        title.className = 'ad-modal-code';
        title.textContent = slot.name;
        box.appendChild(title);
        [['Size', slot.size], ['Placement', slot.placement], ['Audience', slot.reach]].forEach(([label, value]) => {
            if (!value) return;
            const p = document.createElement('p');
            const b = document.createElement('b');
            b.textContent = `${label}: `;
            p.appendChild(b);
            p.appendChild(document.createTextNode(value));
            box.appendChild(p);
        });
        const hint = document.createElement('p');
        hint.className = 'ad-modal-hint';
        hint.textContent = 'Rates are negotiated per campaign. Share the budget you have in mind and you will get availability, creative specs and terms by email.';
        box.appendChild(hint);
    }

    setEnquiryStatus('', '');
    adModal.classList.add('open');
    trackEvent('ad_booking_opened', { slot: slot.name });
    const brandInput = document.getElementById('ad-brand');
    if (brandInput) brandInput.focus();
}

function closeAdBooking() {
    if (adModal) adModal.classList.remove('open');
}

document.addEventListener('click', (e) => {
    const btn = e.target.closest('.ad-book-btn');
    if (btn) openAdBooking(btn.dataset.slot);
});

const adModalClose = document.getElementById('ad-modal-close');
if (adModalClose) adModalClose.addEventListener('click', closeAdBooking);
if (adModal) {
    adModal.addEventListener('click', (e) => { if (e.target === adModal) closeAdBooking(); });
}

if (adForm) {
    adForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const payload = {
            brand: document.getElementById('ad-brand').value.trim(),
            email: document.getElementById('ad-email').value.trim(),
            budget: parseInt(document.getElementById('ad-budget').value, 10),
            currency: document.getElementById('ad-currency').value,
            cycle: document.getElementById('ad-cycle').value,
            message: document.getElementById('ad-message').value.trim(),
            slot_key: adSlotInput ? adSlotInput.value : '',
            company_website: document.getElementById('ad-company-website').value
        };

        if (!payload.brand || !payload.email || !payload.budget || !payload.message) {
            setEnquiryStatus('Brand, email, budget and message are all required.', 'error');
            return;
        }

        if (adSubmitBtn) {
            adSubmitBtn.disabled = true;
            adSubmitBtn.textContent = 'Sending...';
        }
        setEnquiryStatus('Sending your enquiry...', 'pending');

        fetch('/api/v1/enquiries', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
            body: JSON.stringify(payload)
        })
            .then((res) => res.json().catch(() => ({})).then((body) => {
                if (!res.ok || body.ok !== true) {
                    throw new Error(body.error || (body.detail && body.detail[0] && body.detail[0].msg) || `Request failed (${res.status})`);
                }
                return body;
            }))
            .then(() => {
                setEnquiryStatus('Enquiry received. You will get a reply within 24 hours.', 'success');
                showToast('Enquiry sent');
                trackEvent('ad_enquiry_sent', { slot: payload.slot_key || 'exclusive', currency: payload.currency });
                adForm.reset();
                setTimeout(() => { closeAdBooking(); setEnquiryStatus('', ''); }, 2200);
            })
            .catch((err) => {
                setEnquiryStatus(`Could not send the enquiry (${err.message}). Please email directly.`, 'error');
            })
            .then(() => {
                if (adSubmitBtn) {
                    adSubmitBtn.disabled = false;
                    adSubmitBtn.textContent = 'Send Enquiry';
                }
            });
    });
}

/* --------------------------------------------------------------- terminal */

const cliModal = document.getElementById('cli-modal');
const cliTrigger = document.getElementById('cli-trigger');
const cliClose = document.getElementById('cli-close');
const cliInput = document.getElementById('cli-input');
const cliOutput = document.getElementById('cli-output');

if (cliTrigger && cliModal) {
    cliTrigger.addEventListener('click', () => {
        cliModal.classList.add('open');
        if (cliInput) cliInput.focus();
    });
}
if (cliClose && cliModal) cliClose.addEventListener('click', () => cliModal.classList.remove('open'));

document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    closeAdBooking();
    if (cliModal) cliModal.classList.remove('open');
});

function printCliLine(text, isCmd = false) {
    if (!cliOutput) return;
    const line = document.createElement('div');
    line.className = isCmd ? 'cli-line user-cmd' : 'cli-line';
    line.innerHTML = text;
    cliOutput.appendChild(line);
    cliOutput.scrollTop = cliOutput.scrollHeight;
}

const CLI_COMMANDS = {
    help: () => `Available commands:
  <span class="cli-highlight">about</span>      - Who I am
  <span class="cli-highlight">experience</span> - Roles and companies
  <span class="cli-highlight">projects</span>   - Production work
  <span class="cli-highlight">skills</span>     - Technical stack
  <span class="cli-highlight">bucket</span>     - Skills and goals in progress
  <span class="cli-highlight">ads</span>        - Advertisement board status
  <span class="cli-highlight">contact</span>    - How to reach me
  <span class="cli-highlight">clear</span>      - Clear the console
  <span class="cli-highlight">exit</span>       - Close the console`,

    about: () => `${SITE.owner || ''}${SITE.location ? ` - ${SITE.location}` : ''}
${(document.querySelector('.hero-desc') || {}).textContent || ''}`.trim(),

    experience: () => (SITE.experience || [])
        .map((e, i) => `${i + 1}. <span class="cli-highlight">${e.company}</span> (${e.period}): ${e.role}`)
        .join('\n') || 'No roles published.',

    projects: () => (SITE.projects || [])
        .map((p, i) => `${i + 1}. <span class="cli-highlight">${p.title}</span>${p.badge ? ` [${p.badge}]` : ''}${p.link ? ` -> ${p.link}` : ''}`)
        .join('\n') || 'No projects published.',

    skills: () => (SITE.skills || [])
        .map((g) => `<span class="cli-highlight">${g.group}</span>: ${g.items.join(', ')}`)
        .join('\n') || 'No skills published.',

    bucket: () => (SITE.bucket || [])
        .map((b) => {
            const filled = Math.round(b.progress / 10);
            const bar = '#'.repeat(filled) + '.'.repeat(10 - filled);
            return `  [${b.type === 'skill' ? 'SKILL' : ' GOAL'}] ${bar} ${String(b.progress).padStart(3)}%  ${b.title} (${b.target})`;
        })
        .join('\n') || 'Bucket is empty.',

    ads: () => (SITE.adSlots || [])
        .map((s) => `  ${s.status === 'booked' ? '<span class="cli-highlight">[BOOKED]</span>' : '<span class="cli-error">[TO-LET]</span>'} ${s.name} - ${s.size}`)
        .join('\n') || 'No ad slots configured.',

    contact: () => `Email: ${SITE.email || '-'}
Phone: ${SITE.phone || '-'}
Location: ${SITE.location || '-'}
LinkedIn: ${SITE.linkedin || '-'}`
};

const CLI_ALIASES = { bio: 'about', roles: 'experience', goals: 'bucket', advertise: 'ads' };

function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

function handleCliCommand(rawCmd) {
    const cmd = CLI_ALIASES[rawCmd] || rawCmd;
    if (!cmd) return;
    const echo = escapeHtml(rawCmd);
    printCliLine(`<span class="cli-prompt">visitor@portfolio:~$</span> ${echo}`, true);

    if (cmd === 'clear') {
        cliOutput.innerHTML = '<div class="cli-line sys-line">SYSTEM READY. Type <span class="cli-cmd">help</span> for available commands.</div>';
        return;
    }
    if (cmd === 'exit') {
        cliModal.classList.remove('open');
        return;
    }

    const handler = CLI_COMMANDS[cmd];
    if (!handler) {
        printCliLine(`Command not recognised: '<span class="cli-error">${echo}</span>'. Type <span class="cli-cmd">help</span>.`);
        return;
    }
    printCliLine(handler());

    if (cmd === 'bucket' && document.getElementById('bucket')) {
        document.getElementById('bucket').scrollIntoView({ behavior: 'smooth' });
    }
    if (cmd === 'ads' && document.getElementById('adboard')) {
        document.getElementById('adboard').scrollIntoView({ behavior: 'smooth' });
    }
}

if (cliInput) {
    cliInput.addEventListener('keydown', (e) => {
        if (e.key !== 'Enter') return;
        const value = cliInput.value.trim().toLowerCase();
        cliInput.value = '';
        handleCliCommand(value);
    });
}
