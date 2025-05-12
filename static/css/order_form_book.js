

    function checkQuantity() {
        var quantity = parseInt(document.getElementById('id_quantity').value);
        var availableQuantity = parseInt('{{ book.quantity }}');

        if (isNaN(quantity)) {
            alert("Please enter a valid quantity.");
            return false;
        }

        if (quantity <= 0) {
            alert("Please enter a positive quantity.");
            return false;
        }

        if (quantity > availableQuantity) {
            document.getElementById('popup').style.display = 'flex'; /* Display popup */
            return false;
        }

        return true;
    }

    function closePopup() {
        document.getElementById('popup').style.display = 'none'; /* Hide popup */
    }
