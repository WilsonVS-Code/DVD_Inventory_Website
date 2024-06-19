// Forgot Password
document.querySelector('.forgot-password').addEventListener('click', function(event) {
    event.preventDefault();
    alert('Forgot Password functionality to be implemented.');
});


// script.js
document.addEventListener('DOMContentLoaded', function() {
    const hamburgerBtn = document.querySelector('.hamburger');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');

    hamburgerBtn.addEventListener('click', function() {
        sidebar.classList.toggle('expanded');
        mainContent.classList.toggle('expanded');
    });
});


