document.addEventListener('DOMContentLoaded', function() {
    
    var amounts = document.querySelectorAll('.amount');   
   
    amounts.forEach(function(amount) {

        var text = amount.textContent.trim();

        if (text.startsWith('-')) {

            amount.style.color = 'red';

        } else {

            amount.style.color = 'green';
            
        }

    });
});
