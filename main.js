/************************************************************
 * 1) Landing Page Logic
 ************************************************************/
const introVideo = document.getElementById('intro-video');
const mainContent = document.getElementById('main-content');

// Buttons
const listenBtn = document.getElementById('listen-btn');
const joinBtn = document.getElementById('join-btn');

/* Contact toggle elements */
const contactToggleBtn = document.getElementById('contact-toggle-btn');
const contactInfo = document.getElementById('contact-info');

// Start the video halfway through
if (introVideo) {
  introVideo.addEventListener('loadedmetadata', () => {
    introVideo.currentTime = introVideo.duration / 2;
  });

  introVideo.addEventListener('ended', () => {
    // Hide video
    document.getElementById('video-container').style.display = 'none';
    // Show main content
    mainContent.classList.remove('hidden');

    // Fade in buttons:
    // 1) Make the "listen" button visible after 1 second
    setTimeout(() => {
      listenBtn.classList.remove('button-hidden');
      listenBtn.classList.add('button-shown');

      // 2) Then the "join" button 0.5s later
      setTimeout(() => {
        joinBtn.classList.remove('button-hidden');
        joinBtn.classList.add('button-shown');
      }, 500);
    }, 1000);
  });
}

/* Contact dropdown toggle */
if (contactToggleBtn) {
  contactToggleBtn.addEventListener('click', () => {
    if (contactInfo.classList.contains('hidden')) {
      contactInfo.classList.remove('hidden');
    } else {
      contactInfo.classList.add('hidden');
    }
  });
}

/************************************************************
 * 2) Store Page Logic
 ************************************************************/
let cart = [];

/** Adds an item to the cart array */
function addToCart(itemName) {
  cart.push(itemName);
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
