/************************************************************
 * 1) Landing Page Logic
 ************************************************************/
const introVideo = document.getElementById('intro-video');
const mainContent = document.getElementById('main-content');
const contactToggleBtn = document.getElementById('contact-toggle-btn');
const contactInfo = document.getElementById('contact-info');
const listenBtn = document.getElementById('listen-btn');
const joinBtn = document.getElementById('join-btn');

// Start video halfway through
if (introVideo) {
  introVideo.addEventListener('loadedmetadata', () => {
    introVideo.currentTime = introVideo.duration / 2; // Start at halfway point
  });

  introVideo.addEventListener('ended', () => {
    // Hide video container
    document.getElementById('video-container').style.display = 'none';
    // Show main content
    mainContent.classList.remove('hidden');

    // Initially hide the buttons to control their appearance manually
    listenBtn.style.display = 'none';
    joinBtn.style.display = 'none';

    // Delay the button appearances
    setTimeout(() => {
      listenBtn.style.display = 'block'; // Show Listen button
      setTimeout(() => {
        joinBtn.style.display = 'block'; // Show Join button
      }, 500); // 0.5 seconds after the Listen button
    }, 1000); // 1 second after the main content
  });
}

// Toggle contact dropdown
if (contactToggleBtn) {
  contactToggleBtn.addEventListener('click', () => {
    if (contactInfo.classList.contains('hidden')) {
      contactInfo.classList.remove('hidden');
    } else {
      contactInfo.classList.add('hidden');
    }
  });
}

// Listen button -> Linktree
if (listenBtn) {
  listenBtn.addEventListener('click', () => {
    window.open('YOUR_LINKTREE_URL', '_blank'); // Replace with your actual Linktree link
  });
}

// Join button -> Store Page
if (joinBtn) {
  joinBtn.addEventListener('click', () => {
    window.location.href = 'store.html';
  });
}

/************************************************************
 * 2) Store Page Logic
 ************************************************************/
let cart = [];

/**
 * Adds an item to the cart array
 */
function addToCart(itemName) {
  cart.push(itemName);
  alert(`${itemName} added to cart`);
}

/************************************************************
 * 3) Checkout Page Logic
 ************************************************************/
function prepareFormData(event) {
  // If we want to pass cart items to Netlify forms
  const hiddenCartField = document.getElementById('cart-items');
  if (hiddenCartField) {
    hiddenCartField.value = cart.join(', ');
  }
  // The form will then submit to Netlify
}
