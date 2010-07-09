
$('#comment-preview').click(function(){
    var name = $("#id_name").val();
    var url = $("#id_url").val();
    var email = $('#id_email').val();
    var comment = $("#id_content").val();

    data = {'name':name, 'url':url, 'email':email, 'bbcode':comment };
    $('#comment-preview-working').show();
    $("#comment-preview-content").hide();
    var xhr_preview = $("#xhr_preview_comment").val();
    $("#comment-preview-content").load(xhr_preview, data, function(){
        $('#comment-preview-working').hide();
        $("#comment-preview-content").show();

        });
    return false;
});

$('#comment-submit').click(function(){

    var data = {};
    $('#comment-form input, #comment-form textarea').each(function(){
        var $this = $(this);
        var name = $this.attr('name');
        var value = $this.val();
        data[name]=value;

    });

    $('#comment-submit').hide();
    $('#comment-submit-working').show();

    var xhr_post = $("#xhr_post_comment").val();
    $.post(xhr_post, data, function(json){

        var response = eval("("+json+")");
        if (response.status=='ok')
        {
            window.location.href = response.fwd;
        }
        else
        {
            $('#comment-submit-working').hide();
            $('#comment-submit').show();

            $('.comment-form-errors').html('')

            for (error in response.errors)
            {
                var error_id = "#id_" + error + "_errors";
                $(error_id).html(response.errors[error]);
            }
        }

    });

    return false;
});


function delete_comment(comment_id, url)
{
    var data = {'comment_id':comment_id, 'url':url};

    var xhr_delete_comment = $('#xhr_delete_comment').val();

    $.getJSON(xhr_delete_comment, data, function(json){
        if (json.result=="success")
        {
            $('#comment'+comment_id).fadeOut('slow');
        }
        else
        {
            alert("Unable to delete this comment.");
        }
    })
}
