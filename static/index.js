document.addEventListener('DOMContentLoaded', () => {

    function handleClick() {
        document.getElementById('spinner').style.visibility = 'visible';
    }

    var last_img_id = 0;
    var waiting = false;

    console.log(window.location.href);
    const host = "http://art-intel.site/";
    // JAVASCRIPT FOR INDEX PAGE
    if (window.location.href == host + 'index.html') {
        console.log("this is index page");
    }
    // JAVASCRIPT FOR ORDER PAGE
    if (window.location.href == host + 'order.html') {
        console.log("this is order page");
    }


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
                    // create new image node
                    var new_image = document.createElement('div');
                    // add title
                    new_image.innerHTML += "<center><h3>" + images[i]['title'] + "</h3></center>";
                    new_image.classList.add('image_field');
                    // add image
                    var img = document.createElement('img');
                    img.src = "data:image;base64," + images[i]['data'];
                    new_image.appendChild(img);
                    // add delete link

                    var del_text = document.createElement('a');
                    del_text.href = "/delete?img_id=" + images[i]["image_id"];
                    del_text.appendChild(document.createTextNode("Delete"));
                    new_image.appendChild(del_text);

                    //textNode.a.href = "/delete?img_id=" + images[i]["image_id"];
                    //new_image.appendChild(textNode);

                    document.getElementById('image_child').appendChild(new_image);
                }
                last_img_id = images[images.length-1]["image_id"];
                //document.querySelector('#image_child').innerHTML += all_nodes;
                document.getElementById('spinner').style.visibility = 'hidden';
                waiting = false;

            });

        }
    }
});