bridge_ip = "";
username = "";
connected = false;

function show_screen(filename) {
	jQuery('#still')[0].src = filename;
}

function connect() {
	bridge_ip = jQuery("input#bridge_ip").val();
	username = jQuery("input#username").val();

	jQuery("span#status").html("connecting");
	jQuery.get("http://" + bridge_ip + "/api/" + username, function(data) {
		if (data.hasOwnProperty('lights')) {
			jQuery("span#status").html("connected");
			connected = true;
		} else if (data[0].hasOwnProperty('error')) {
			jQuery("span#status").html(data[0].error['description']);
		} else {
			jQuery("span#status").html("failed");
		}
	})
	.fail(function() {
		jQuery("span#status").html("failed");
	})
}

function set_light(h, s, v) {
	if (connected == true) {
		light = jQuery("input:radio[name=light]:checked").val();
		bri = v;
		url = "http://" + bridge_ip + "/api/" + username + "/lights/" + light + "/state";
		data = '{"on": true, "hue": '+h+', "sat": '+s+', "bri": '+bri+'}';
		jQuery("span#status").html(data);
		jQuery.ajax({	url: url, type: "PUT", data: data,
			succes: function(data) {
				if (data[0].hasOwnProperty('error')) {
					console.log(data[0].error['description']);
				}
			}
		});
	}
}