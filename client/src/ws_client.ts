import * as WebSocket from 'ws';


let socket = new WebSocket('ws://127.0.0.1:3000');
let st = WebSocket.createWebSocketStream(socket, {encoding: 'utf-8'});
socket.on('open', function open() {
	socket.send('something\r\n{"jsonrpc":"2.0","id":2,"method":"initialize"}');
	// st.write('{"jsonrpc":"2.0","id":2,"method":"initialize"}');
});
socket.on('message', (data) => {
	console.log(data);
	console.log(st.read());
});

// st.write('{"jsonrpc":"2.0","id":2,"method":"initialize"}');
// console.log(st.read());