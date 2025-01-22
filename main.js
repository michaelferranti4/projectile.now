/************************************************************
 * 1) Landing Page Logic
 ************************************************************/
const introVideo = document.getElementById('intro-video');
const mainContent = document.getElementById('main-content');

// Buttons
const listenBtn = document.getElementById('listen-btn');
const joinBtn = document.getElementById('join-btn');

// Contact container & toggle
const contactContainer = document.getElementById('contact-container');
const contactToggleBtn = document.getElementById('contact-toggle-btn');
const contactInfo = document.getElementById('contact-info');

// If the video is loaded, start it halfway
if (introVideo) {
  introVideo.addEventListener('loadedmetadata', () => {
    introVideo.currentTime = introVideo.duration / 2;
  });

  // Skip the intro if user clicks the video container
  introVideo.addEventListener('click', skipIntroVideo);

  // When the video ends, skip normally
  introVideo.addEventListener('ended', () => {
    skipIntroVideo();
  });
}

/**
 * The function that runs after the user or natural end event
 * (We "simulate" the same actions as if the video ended).
 */
function skipIntroVideo() {
  // Remove video container
  document.getElementById('video-container').style.display = 'none';
  // Show main content
  mainContent.classList.remove('hidden');

  // Fade in first button (Listen) after 1s
  setTimeout(() => {
    listenBtn.classList.remove('button-hidden');
    listenBtn.classList.add('button-shown');

    // Fade in second button (Join) after 0.5s
    setTimeout(() => {
      joinBtn.classList.remove('button-hidden');
      joinBtn.classList.add('button-shown');

      // Fade in Contact button 1s after the Join button
      setTimeout(() => {
        contactContainer.classList.remove('button-hidden');
        contactContainer.classList.add('button-shown');
      }, 1000);

    }, 500);
  }, 1000);
}

// Listen button -> Linktree
if (listenBtn) {
  listenBtn.addEventListener('click', () => {
    window.open('https://linktr.ee/kidsmoko', '_blank');
  });
}

// Join button -> Store Page
if (joinBtn) {
  joinBtn.addEventListener('click', () => {
    window.location.href = 'store.html';
  });
}

/* Contact dropdown toggle */
if (contactToggleBtn) {
  contactToggleBtn.addEventListener('click', () => {
    contactInfo.classList.toggle('hidden');
  });
}

/************************************************************
 * 2) Store Page Logic
 ************************************************************/
let cart = JSON.parse(localStorage.getItem('cart')) || [];

/** Adds an item to the cart array and saves it in localStorage */
function addToCart(itemName) {
  cart.push(itemName);
  // Save to localStorage so we still have the cart on checkout.html
  localStorage.setItem('cart', JSON.stringify(cart));
  alert(`${itemName} added to cart`);
}

/************************************************************
 * 3) Checkout Page Logic
 ************************************************************/
function prepareFormData(event) {
  // If we want to pass cart items to Netlify forms:
  const hiddenCartField = document.getElementById('cart-items');
  if (hiddenCartField) {
    hiddenCartField.value = cart.join(', ');
  }
  // The form will then submit to Netlify
}
