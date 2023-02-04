function handleClick() {
    document.getElementById('spinner').style.visibility = 'visible';
}

var last_img_id = 0;

// window scroll detect
window.onscroll = function() {

    if (window.innerHeight + window.pageYOffset >= document.body.offsetHeight) {
        var socket = io();
        // websockets send more images
        socket.on('connect', function() {
            socket.emit('my_event', {data: last_img_id});
        });

        socket.on('image feed', images => {
            //alert(images['title']);
            images.forEach(add_image);
        });
    }

    // Add a new post with given contents to DOM.
    // const post_template = Handlebars.compile(document.querySelector('#post').innerHTML);
    function add_image(image) {
        console.log(image['title'])
        last_img_id = image["image_id"]
        // Create new post.
        // Handlebars
        // const img = post_template({'title':data["user"], 'img_data': data["img_data"]});

        // Add post to DOM.
        document.querySelector('#image_child').innerHTML += "<div class='image_field'><h3>" + image['title'] + "</h3></center><img src='data:;base64," + image['rendered_data'] + "'/></div>"
    }
}
