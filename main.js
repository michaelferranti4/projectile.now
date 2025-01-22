/************************************************************
 * 1) Landing Page Logic
 ************************************************************/
const introVideo = document.getElementById('intro-video');
const mainContent = document.getElementById('main-content');
const listenBtn = document.getElementById('listen-btn');
const joinBtn = document.getElementById('join-btn');

// Start video halfway through
if (introVideo) {
  introVideo.addEventListener('loadedmetadata', () => {
    // Force the video to start from halfway point every time
    introVideo.currentTime = introVideo.duration / 2;
  });

  introVideo.addEventListener('ended', () => {
    // Hide video container
    document.getElementById('video-container').style.display = 'none';
    // Show main content
    mainContent.classList.remove('hidden');

    // Initially hide the buttons
    listenBtn.style.display = 'none';
    joinBtn.style.display = 'none';

    // Delay the button appearances
    setTimeout(() => {
      listenBtn.style.display = 'inline-block'; // Show Listen button
      setTimeout(() => {
        joinBtn.style.display = 'inline-block'; // Show Join button
      }, 500); // 0.5 seconds after Listen
    }, 1000); // 1 second after main content
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
