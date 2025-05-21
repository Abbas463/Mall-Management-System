// Additional JavaScript functions can be added here
document.addEventListener('DOMContentLoaded', function() {
    // Print bill functionality
    document.querySelectorAll('.print-bill').forEach(button => {
        button.addEventListener('click', function() {
            window.print();
        });
    });
    
    // Toggle password visibility
    document.querySelectorAll('.toggle-password').forEach(button => {
        button.addEventListener('click', function() {
            const input = this.previousElementSibling;
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);
            this.textContent = type === 'password' ? 'Show' : 'Hide';
        });
    });
});