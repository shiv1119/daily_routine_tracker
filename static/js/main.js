// Main JavaScript for Daily Routine Tracker

// Dark Mode Toggle
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });
    
    // Auto-save functionality for tracker
    const autoSaveForms = document.querySelectorAll('.auto-save');
    autoSaveForms.forEach(form => {
        form.addEventListener('change', function() {
            saveForm(this);
        });
    });
    
    // Rank-up notification
    checkRankUp();
});

// Function to save form via AJAX
function saveForm(form) {
    const formData = new FormData(form);
    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Saved successfully!', 'success');
        } else {
            showNotification('Error saving data', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Network error', 'error');
    });
}

// Function to show notifications
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification alert alert-${type}`;
    notification.innerHTML = `
        <i class="fas ${getIconForType(type)}"></i>
        ${message}
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

function getIconForType(type) {
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    return icons[type] || icons.info;
}

// Function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Check for rank up
function checkRankUp() {
    const rankBadge = document.querySelector('.rank-badge');
    if (rankBadge && !sessionStorage.getItem('rankNotified')) {
        const currentRank = rankBadge.textContent;
        const previousRank = localStorage.getItem('previousRank');
        
        if (previousRank && previousRank !== currentRank) {
            // Rank up detected
            rankBadge.classList.add('rank-up');
            showNotification(`🎉 Congratulations! You've reached ${currentRank}! 🎉`, 'success');
            
            // Play sound if supported
            if (window.AudioContext || window.webkitAudioContext) {
                playRankUpSound();
            }
            
            setTimeout(() => {
                rankBadge.classList.remove('rank-up');
            }, 600);
        }
        
        localStorage.setItem('previousRank', currentRank);
        sessionStorage.setItem('rankNotified', 'true');
    }
}

// Play rank up sound
function playRankUpSound() {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = 880;
    gainNode.gain.value = 0.1;
    
    oscillator.start();
    setTimeout(() => {
        oscillator.stop();
    }, 500);
}

// Mobile sidebar toggle
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('show');
}

// Add event listener for mobile menu button
document.addEventListener('DOMContentLoaded', function() {
    const menuButton = document.querySelector('.mobile-menu-btn');
    if (menuButton) {
        menuButton.addEventListener('click', toggleSidebar);
    }
});

// Progress bar animation
function animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0%';
        setTimeout(() => {
            bar.style.width = width;
        }, 100);
    });
}

// Call on page load
window.addEventListener('load', animateProgressBars);

// Chart refresh function
function refreshCharts() {
    const charts = Chart.instances;
    Object.values(charts).forEach(chart => {
        chart.update();
    });
}

// Auto-refresh data every 5 minutes
setInterval(() => {
    if (window.location.pathname === '/dashboard/') {
        location.reload();
    }
}, 300000);

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl + S to save
    if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        const saveButton = document.querySelector('button[type="submit"]');
        if (saveButton) {
            saveButton.click();
        }
    }
    
    // Ctrl + D for dashboard
    if (e.ctrlKey && e.key === 'd') {
        e.preventDefault();
        window.location.href = '/dashboard/';
    }
    
    // Ctrl + T for tracker
    if (e.ctrlKey && e.key === 't') {
        e.preventDefault();
        window.location.href = '/tracker/';
    }
});

// Confirmation for destructive actions
document.querySelectorAll('.confirm-delete').forEach(button => {
    button.addEventListener('click', function(e) {
        if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
            e.preventDefault();
        }
    });
});

// Lazy loading for images
const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const img = entry.target;
            img.src = img.dataset.src;
            observer.unobserve(img);
        }
    });
});

document.querySelectorAll('img[data-src]').forEach(img => {
    imageObserver.observe(img);
});