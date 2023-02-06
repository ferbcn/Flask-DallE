var waiting = false;
var last_img_id = 0;

var socket = io();

function handleDelete(image_id){

        const image = document.getElementById(image_id);
        const list = document.getElementById("image_child");
        list.removeChild(image);
        socket.emit('delete_event', {data: image_id});
    }

// window scroll detect
window.onscroll = function() {

    if (window.innerHeight + window.pageYOffset >= document.body.offsetHeight && !waiting) {

        //var socket = io();
        // websockets send more images
        socket.emit('my_event', {data: last_img_id});
        waiting = true;

        var element = document.getElementById("spinner");
        element.style.position = "absolut";
        element.style.top = "500px";
        element.style.visibility = 'visible';

    }
}

// load image feed
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
        var img_id = images[i]['image_id'];
        del_text.href = "javascript:handleDelete(" + img_id + ")";
        del_text.appendChild(document.createTextNode("Delete"));
        new_image.appendChild(del_text);
        new_image.id = img_id

        const list = document.getElementById("image_child");
        // delete first entry in image list before we add the next
        // list.removeChild(list.firstElementChild);
        list.appendChild(new_image);

    }
    last_img_id = images[images.length-1]["image_id"];
    //document.querySelector('#image_child').innerHTML += all_nodes;
    document.getElementById('spinner').style.visibility = 'hidden';
    waiting = false;

});


document.addEventListener("DOMContentLoaded", function(event) {
    /*
    - Code to execute when only the HTML document is loaded.
    - This doesn't wait for stylesheets,
      images, and subframes to finish loading.
    */

    // remove "zombie" child from image list
    //const list = document.getElementById("image_child");
    //list.removeChild(list.lastChild);
    // and get teh id of last image in list
    //last_img_id = document.getElementById("image_child").lastChild.id;
    last_img_id = document.getElementById("image_child").lastChild.previousSibling.id;
});

