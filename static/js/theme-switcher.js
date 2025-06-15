// static/js/theme-switcher.js

(() => {
    'use strict';

    // Function to get the stored theme from localStorage
    const getStoredTheme = () => localStorage.getItem('theme');

    // Function to set the theme in localStorage
    const setStoredTheme = theme => localStorage.setItem('theme', theme);

    // Function to determine the preferred theme
    const getPreferredTheme = () => {
        const storedTheme = getStoredTheme();
        if (storedTheme) {
            return storedTheme;
        }
        // Fallback to user's OS preference
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    };

    // Function to set the theme on the <html> element
    const setTheme = theme => {
        document.documentElement.setAttribute('data-bs-theme', theme);
    };

    // Set the theme on initial load
    setTheme(getPreferredTheme());

    // Add event listener for the theme switcher button
    window.addEventListener('DOMContentLoaded', () => {
        const themeSwitcher = document.getElementById('theme-switcher');
        
        if (themeSwitcher) {
            // Update the icon on load
            const currentTheme = getPreferredTheme();
            if (currentTheme === 'dark') {
                themeSwitcher.innerHTML = '<i class="bi bi-sun-fill"></i>';
            } else {
                themeSwitcher.innerHTML = '<i class="bi bi-moon-fill"></i>';
            }

            // Add click event
            themeSwitcher.addEventListener('click', () => {
                const currentTheme = getStoredTheme() || getPreferredTheme();
                const newTheme = currentTheme === 'light' ? 'dark' : 'light';
                setStoredTheme(newTheme);
                setTheme(newTheme);
                
                // Update the icon on click
                if (newTheme === 'dark') {
                    themeSwitcher.innerHTML = '<i class="bi bi-sun-fill"></i>';
                } else {
                    themeSwitcher.innerHTML = '<i class="bi bi-moon-fill"></i>';
                }
            });
        }
    });
})();