
$(function(){
    $('div[id^=oi-]').each(function(){

        var name = $(this).attr('id').substr(3);
        $('#oiarea-'+name).mouseover(function(){
           var h = $('#oi-'+name+' .image-overlay .caption').height();
           $('#oi-'+name+' .overlay-outer').animate({
            'top':-h
           }, { queue:false, duration:300 }, 'swing');

        });
        $('#oiarea-' + name).mouseout(function(){
           $('#oi-' + name +' .overlay-outer').animate({
                'top':0
           }, { queue:false, duration:300 }, 'swing');

        });
    });
});
