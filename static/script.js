// JavaScript for Ticketing System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Form validation
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Confirm dialogs for dangerous actions
    var confirmButtons = document.querySelectorAll('[data-confirm]');
    confirmButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            var message = button.getAttribute('data-confirm');
            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });

    // Auto-refresh dashboard every 30 seconds
    if (window.location.pathname === '/dashboard') {
        setInterval(function() {
            // Only refresh if the page is visible
            if (!document.hidden) {
                location.reload();
            }
        }, 30000);
    }

    // Live search functionality
    var searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            var filter = this.value.toLowerCase();
            var tickets = document.querySelectorAll('.ticket-item');
            
            tickets.forEach(function(ticket) {
                var title = ticket.querySelector('.ticket-title').textContent.toLowerCase();
                var description = ticket.querySelector('.ticket-description').textContent.toLowerCase();
                
                if (title.includes(filter) || description.includes(filter)) {
                    ticket.style.display = '';
                } else {
                    ticket.style.display = 'none';
                }
            });
        });
    }

    // Priority color coding
    function updatePriorityColors() {
        var priorityElements = document.querySelectorAll('[data-priority]');
        priorityElements.forEach(function(element) {
            var priority = element.getAttribute('data-priority');
            element.classList.add('priority-' + priority);
        });
    }
    updatePriorityColors();

    // Status color coding
    function updateStatusColors() {
        var statusElements = document.querySelectorAll('[data-status]');
        statusElements.forEach(function(element) {
            var status = element.getAttribute('data-status').replace(' ', '-');
            element.classList.add('status-' + status);
        });
    }
    updateStatusColors();

    // Character counter for text areas
    var textAreas = document.querySelectorAll('textarea[maxlength]');
    textAreas.forEach(function(textArea) {
        var maxLength = textArea.getAttribute('maxlength');
        var counter = document.createElement('div');
        counter.className = 'character-counter text-muted small';
        counter.style.textAlign = 'right';
        textArea.parentNode.appendChild(counter);

        function updateCounter() {
            var remaining = maxLength - textArea.value.length;
            counter.textContent = remaining + ' characters remaining';
            
            if (remaining < 50) {
                counter.classList.add('text-warning');
            } else {
                counter.classList.remove('text-warning');
            }
        }

        textArea.addEventListener('input', updateCounter);
        updateCounter();
    });

    // Quick status update
    var statusSelects = document.querySelectorAll('.quick-status-update');
    statusSelects.forEach(function(select) {
        select.addEventListener('change', function() {
            var ticketId = this.getAttribute('data-ticket-id');
            var newStatus = this.value;
            
            // Show loading state
            this.disabled = true;
            
            // Create form data
            var formData = new FormData();
            formData.append('status', newStatus);
            
            // Send update request
            fetch('/update_ticket/' + ticketId, {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (response.ok) {
                    // Show success message
                    showNotification('Ticket status updated successfully!', 'success');
                    
                    // Update UI
                    var statusBadge = document.querySelector(`[data-ticket="${ticketId}"] .status-badge`);
                    if (statusBadge) {
                        statusBadge.textContent = newStatus;
                        statusBadge.className = 'badge status-badge status-' + newStatus.replace(' ', '-');
                    }
                } else {
                    showNotification('Failed to update ticket status.', 'error');
                    // Revert select value
                    this.value = this.getAttribute('data-original-value');
                }
            })
            .catch(error => {
                showNotification('An error occurred while updating the ticket.', 'error');
                this.value = this.getAttribute('data-original-value');
            })
            .finally(() => {
                this.disabled = false;
            });
        });
    });

    // Notification system
    function showNotification(message, type = 'info') {
        var alertClass = 'alert-' + (type === 'error' ? 'danger' : type);
        var alertHtml = `
            <div class="alert ${alertClass} alert-dismissible fade show notification" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        var container = document.querySelector('.container');
        if (container) {
            container.insertAdjacentHTML('afterbegin', alertHtml);
            
            // Auto-hide after 3 seconds
            setTimeout(function() {
                var notification = document.querySelector('.notification');
                if (notification) {
                    var bsAlert = new bootstrap.Alert(notification);
                    bsAlert.close();
                }
            }, 3000);
        }
    }

    // File upload handling
    var fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            var fileName = this.files[0] ? this.files[0].name : 'No file chosen';
            var label = this.nextElementSibling;
            if (label && label.classList.contains('custom-file-label')) {
                label.textContent = fileName;
            }
        });
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        // Ctrl+N or Cmd+N for new ticket
        if ((event.ctrlKey || event.metaKey) && event.key === 'n') {
            event.preventDefault();
            var createButton = document.querySelector('[href*="create_ticket"]');
            if (createButton) {
                createButton.click();
            }
        }
        
        // Escape to close modals
        if (event.key === 'Escape') {
            var modals = document.querySelectorAll('.modal.show');
            modals.forEach(function(modal) {
                var bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });
        }
    });

    // Smooth scrolling for anchor links
    var anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(function(link) {
        link.addEventListener('click', function(event) {
            var targetId = this.getAttribute('href').substring(1);
            var targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                event.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add loading animation to form submissions
    var forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function() {
            var submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.classList.add('btn-loading');
                submitBtn.disabled = true;
            }
        });
    });
});

// Utility functions
function formatDate(dateString) {
    var date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}