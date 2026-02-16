lucide.createIcons();

// Reveal on Scroll Engine
const revealCallback = (entries, observer) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('active-reveal');
    }
  });
};
const observer = new IntersectionObserver(revealCallback, { threshold: 0.1 });
document
  .querySelectorAll('.reveal, .reveal-left, .reveal-right')
  .forEach((el) => observer.observe(el));

function scrollToId(id) {
  document.getElementById(id).scrollIntoView({ behavior: 'smooth' });
}

function openAim(evt, aimName) {
  document
    .querySelectorAll('.aim-content')
    .forEach((c) => c.classList.remove('active'));
  document
    .querySelectorAll('.aim-pill')
    .forEach((t) => t.classList.remove('active'));
  document.getElementById(aimName).classList.add('active');
  evt.currentTarget.classList.add('active');
}

function toggleFaq(btn) {
  const drawer = btn.nextElementSibling;
  const icon = btn.querySelector('i');
  if (drawer.style.maxHeight) {
    drawer.style.maxHeight = null;
    icon.style.transform = 'rotate(0deg)';
  } else {
    drawer.style.maxHeight = drawer.scrollHeight + 'px';
    icon.style.transform = 'rotate(45deg)';
  }
}

const scrollContainer = document.getElementById('services-container');
const prevBtn = document.getElementById('service-prev');
const nextBtn = document.getElementById('service-next');

if (scrollContainer && prevBtn && nextBtn) {
  const getScrollAmount = () => {
    const card = scrollContainer.querySelector('.service-card');
    const style = window.getComputedStyle(scrollContainer);
    const gap = parseInt(style.gap) || 24;
    return card.offsetWidth + gap;
  };

  nextBtn.addEventListener('click', () => {
    scrollContainer.scrollBy({ left: getScrollAmount(), behavior: 'smooth' });
  });

  prevBtn.addEventListener('click', () => {
    scrollContainer.scrollBy({ left: -getScrollAmount(), behavior: 'smooth' });
  });

  // Button Visibility Logic
  scrollContainer.addEventListener('scroll', () => {
    const scrollLeft = scrollContainer.scrollLeft;
    const maxScroll = scrollContainer.scrollWidth - scrollContainer.clientWidth;
    prevBtn.style.opacity = scrollLeft <= 5 ? '0.3' : '1';
    nextBtn.style.opacity = scrollLeft >= maxScroll - 5 ? '0.3' : '1';
  });
}

// --- DRAG TO SCROLL (DESKTOP) ---
if (scrollContainer) {
  let isDown = false;
  let startX;
  let scrollLeft;

  scrollContainer.addEventListener('mousedown', (e) => {
    isDown = true;
    startX = e.pageX - scrollContainer.offsetLeft;
    scrollLeft = scrollContainer.scrollLeft;
  });

  scrollContainer.addEventListener('mouseleave', () => (isDown = false));
  scrollContainer.addEventListener('mouseup', () => (isDown = false));

  scrollContainer.addEventListener('mousemove', (e) => {
    if (!isDown) return;
    e.preventDefault();
    const x = e.pageX - scrollContainer.offsetLeft;
    const walk = (x - startX) * 2;
    scrollContainer.scrollLeft = scrollLeft - walk;
  });
}

// --- TEAM SNAP SCROLL ENGINE ---
const teamContainer = document.getElementById('team-container');
const teamPrev = document.getElementById('team-prev');
const teamNext = document.getElementById('team-next');

if (teamContainer && teamPrev && teamNext) {
  const getTeamScrollAmount = () => {
    const card = teamContainer.querySelector('.team-card');
    const style = window.getComputedStyle(teamContainer);
    const gap = parseInt(style.gap) || 24;
    return card.offsetWidth + gap;
  };

  teamNext.addEventListener('click', () => {
    teamContainer.scrollBy({ left: getTeamScrollAmount(), behavior: 'smooth' });
  });

  teamPrev.addEventListener('click', () => {
    teamContainer.scrollBy({
      left: -getTeamScrollAmount(),
      behavior: 'smooth',
    });
  });

  // Visibility Logic
  teamContainer.addEventListener('scroll', () => {
    const scrollLeft = teamContainer.scrollLeft;
    const maxScroll = teamContainer.scrollWidth - teamContainer.clientWidth;
    teamPrev.style.opacity = scrollLeft <= 5 ? '0.3' : '1';
    teamNext.style.opacity = scrollLeft >= maxScroll - 5 ? '0.3' : '1';
  });
}

// --- DRAG TO SCROLL (DESKTOP) ---
if (teamContainer) {
  let isDown = false;
  let startX;
  let scrollLeft;

  teamContainer.addEventListener('mousedown', (e) => {
    isDown = true;
    startX = e.pageX - teamContainer.offsetLeft;
    scrollLeft = teamContainer.scrollLeft;
  });

  teamContainer.addEventListener('mouseleave', () => (isDown = false));
  teamContainer.addEventListener('mouseup', () => (isDown = false));

  teamContainer.addEventListener('mousemove', (e) => {
    if (!isDown) return;
    e.preventDefault();
    const x = e.pageX - teamContainer.offsetLeft;
    const walk = (x - startX) * 2;
    teamContainer.scrollLeft = scrollLeft - walk;
  });
}

// Bookings
function selectOpt(btn) {
  document
    .querySelectorAll('.option-card')
    .forEach((c) => c.classList.remove('selected'));
  btn.classList.add('selected');
}
document.querySelectorAll('.slot-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    document
      .querySelectorAll('.slot-btn')
      .forEach((b) => b.classList.remove('active'));
    btn.classList.add('active');
  });
});