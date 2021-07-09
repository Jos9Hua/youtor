$(document).ready(function(){
    // $('.nav-tabs a:first').tab('show');
    // Add smooth scrolling to all links
    $(".scroll-tab").on('click', function(event) {
  
      // Make sure this.hash has a value before overriding default behavior
      if (this.hash !== "") {
        // Prevent default anchor click behavior
  
        // Store hash
        var hash = this.hash;
      if (hash == "#profile-tab"){
      console.log(hash);
    //   $('#home-tab').tab('hide');
      $('#profile-tab').tab('show');

    }else{

        $('#home-tab').tab('show');
      }
       // Using jQuery's animate() method to add smooth page scroll
      // The optional number (800) specifies the number of milliseconds it takes to scroll to the specified area
      $('html, body').animate({
        scrollTop: $(hash).offset().top
      }, 800, function(){
   
        // Add hash (#) to URL when done scrolling (default click behavior)
        window.location.hash = hash;
      });
    } // End if
  });
});