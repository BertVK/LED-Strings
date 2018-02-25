 jQuery(document).ready(function($) {
     $(function() {
         /*
        setInterval(function() {
           $.getJSON($SCRIPT_ROOT + '/_get_temp', {
           }, function(data) {
             $("#temp").text(data.temp);
           });
           return false;
         },5000);
         */
     });
    $(function() {
        $('a#button1').bind('click', function() {
          $.getJSON($SCRIPT_ROOT + '/button1', {
          }, function(data) {
            $("#state").text(data.state);
            $("#stateDescr").text(data.stateDescr);
          });
          return false;
        });
    });
    $(function() {
        $('a#button2').bind('click', function() {
          $.getJSON($SCRIPT_ROOT + '/button2', {
          }, function(data) {
            $("#state").text(data.state);
            $("#stateDescr").text(data.stateDescr);
          });
          return false;
        });
    });
    $(function() {
        $('#brightness').change(function() {
           $.getJSON($SCRIPT_ROOT + '/brightness', {
               brightness: $('input[name="brightness"]').val()
           }, function(data) {
             $('#brightness').val(data.brightness);
             $('#brightnessVal').text(data.brightness);
           });
           return false; 
        });
    });
    $(function() {
        $('#randomOn').change(function(){
           var c = 0;
           if ($('#randomOn').prop('checked')) {
               c = 1;
           } else {
               c = 0;
           }
           $.getJSON($SCRIPT_ROOT + '/randomOn', {
               randomOn: c
           }, function(data) {
              //$('#randomOnStr').text(data.randomOn);
           });
           return false;
        });
    });
 });