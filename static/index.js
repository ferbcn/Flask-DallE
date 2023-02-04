function handleClick() {
    document.getElementById('spinner').style.visibility = 'visible';
}

var last_img_id = 0;
var waiting = false;


// window scroll detect
window.onscroll = function() {

    if (window.innerHeight + window.pageYOffset >= document.body.offsetHeight - 100 && !waiting) {

        var socket = io();
        // websockets send more images
        socket.on('connect', function() {
            socket.emit('my_event', {data: last_img_id});
            waiting = true;
            var element = document.getElementById("spinner");
            element.style.position = "absolut";
            element.style.top = "500px";
            element.style.visibility = 'visible';
        });

        socket.on('image feed', images => {
            //alert(images['title']);
            //images.forEach(add_image);
            var all_nodes = [];
            for (var i=0; i<images.length; i++){
                //var node = "<div class='image_field'><center><h3>" + images[i]['title'] + "</h3></center><img src='data:image;base64," + images[i]['data'] + "'/></div>";
                //all_nodes.push(node);
                var new_image = document.createElement('div');
                new_image.innerHTML += "<center><h3>" + images[i]['title'] + "</h3></center>";

                new_image.classList.add('image_field');

                var img = document.createElement('img');
                img.src = "data:image;base64," + images[i]['data'];
                new_image.appendChild(img);

                document.getElementById('image_child').appendChild(new_image);
            }
            last_img_id = images[images.length-1]["image_id"];
            //document.querySelector('#image_child').innerHTML += all_nodes;
            document.getElementById('spinner').style.visibility = 'hidden';
            waiting = false;

        });

    }
}
