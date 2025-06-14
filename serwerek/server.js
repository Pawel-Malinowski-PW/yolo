const https = require('https');
const fs = require('fs');
const path = require('path');
const WebSocket = require('ws');
const { spawn } = require('child_process'); 

let pythonProcess; // dostęp dla pythona

// Certyfikaty
const options = {
    key: fs.readFileSync(path.join(__dirname, 'server.key')),
    cert: fs.readFileSync(path.join(__dirname, 'server.crt'))
};

// Tworzenie serwera HTTPS
const server = https.createServer(options, (req, res) => {
    let filePath = path.join(__dirname, req.url === '/' ? 'index.html' : req.url);
    const ext = path.extname(filePath);
    let contentType = 'text/html';

    if (ext === '.html') contentType = 'text/html';
    else if (ext === '.js') contentType = 'application/javascript';
    else if (ext === '.css') contentType = 'text/css';

    fs.readFile(filePath, (err, content) => {
        if (err) {
            res.writeHead(404, { 'Content-Type': 'text/plain' });
            res.end('404 Not Found');
        } else {
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(content, 'utf-8');
        }
    });
});

// Tworzenie serwera WebSocket
const wss = new WebSocket.Server({ server });

const clients = {
    stream: null,
    view: [],
    script: null,
    script2: null, // <--- dodaj to pole!
    result: []
};
// zapytanie o zidentyfikowanie się
function sendToClients(clients, data, isBinary) {
    clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(data, { binary: isBinary });
        }
    });
}
// sprawdzenie odpowiedzi stream
function handleStreamMessage(ws, data, isBinary) {
    sendToClients(clients.view, data, isBinary);
    if (clients.script && clients.script.readyState === WebSocket.OPEN) {
        clients.script.send(data, { binary: isBinary });
    }
    if (clients.script2 && clients.script2.readyState === WebSocket.OPEN) {
        clients.script2.send(data, { binary: isBinary });
    }
    if (!pythonProcess && clients.stream && clients.stream.readyState === WebSocket.OPEN) {
        clients.stream.send(data, { binary: isBinary });
    }
}
// sprawdzenie odpowiedzi skrypt
function handleScriptMessage(ws, data, isBinary) {
    sendToClients(clients.result, data, isBinary);
    if (clients.stream && clients.stream.readyState === WebSocket.OPEN) {
        clients.stream.send(data, { binary: isBinary });
    }
}

wss.on('connection', (ws, req) => {
    console.log('WebSocket połączony');

    // Oczekuj identyfikatora klienta jako pierwszej wiadomości
    ws.on('message', (data, isBinary) => {
        if (!ws.role) {
            // Pierwsza wiadomość powinna zawierać rolę klienta
            const role = data.toString();
            ws.role = role; // Przypisz rolę klientowi
            if (role === 'stream') {
                clients.stream = ws;
                console.log('Klient stream połączony');
            } else if (role === 'view') {
                clients.view.push(ws);
                console.log('Klient view połączony');
            } else if (role === 'script') {
                clients.script = ws;
                console.log('Klient script połączony');
            } else if (role === 'script2') {
                clients.script2 = ws; // <--- obsługa nowej roli
                console.log('Klient script2 połączony');
            } else if (role === 'result') {
                clients.result.push(ws);
                console.log('Klient result połączony');
            } else {
                console.error(`Nieznana rola klienta: ${role}`);
            }
            return;
        }

        function startPythonScript(args, env, scriptType) {
            const pythonVenvPath = '/home/malinop4/yolo-venv/bin/python';
            pythonProcess = spawn(pythonVenvPath, args, {
                cwd: __dirname,
                env
            });
            pythonProcess.scriptType = scriptType; // <--- zapamiętaj typ
            pythonProcess.stdout.on('data', (data) => {
                console.log(`${args[0]} stdout: ${data}`);
            });
            pythonProcess.stderr.on('data', (data) => {
                console.error(`${args[0]} stderr: ${data}`);
            });
            pythonProcess.on('close', (code) => {
                console.log(`${args[0]} zakończył pracę z kodem ${code}`);
                pythonProcess = null;
            });
        }

        if (data.toString() === 'start-script') {
            if (pythonProcess && pythonProcess.scriptType === 'script') {
                // YOLOv3 już działa, nie rób nic
                console.log('YOLOv3 już działa, nie restartuję.');
            } else if (pythonProcess) {
                pythonProcess.kill();
                pythonProcess.on('close', () => {
                    startPythonScript(['script.py'], { ...process.env, LD_LIBRARY_PATH: path.join(__dirname, 'darknet/python') }, 'script');
                });
            } else {
                startPythonScript(['script.py'], { ...process.env, LD_LIBRARY_PATH: path.join(__dirname, 'darknet/python') }, 'script');
            }
        } else if (data.toString() === 'stop-script' || data.toString() === 'stop-script2') {
            if (pythonProcess) {
                pythonProcess.kill();
                pythonProcess.on('close', () => {
                    pythonProcess = null;
                    console.log('Proces detekcji został zatrzymany.');
                });
            } else {
                console.log('Brak procesu do zatrzymania.');
            }
        } else if (data.toString() === 'start-script2') {
            if (pythonProcess && pythonProcess.scriptType === 'script2') {
                // YOLOv5 już działa, nie rób nic
                console.log('YOLOv5 już działa, nie restartuję.');
            } else if (pythonProcess) {
                pythonProcess.kill();
                pythonProcess.on('close', () => {
                    startPythonScript(['script2.py'], { ...process.env }, 'script2');
                });
            } else {
                startPythonScript(['script2.py'], { ...process.env }, 'script2');
            }
        } else if (data.toString() === 'stop-script2') {
            if (pythonProcess) {
                console.log('Zatrzymywanie script2.py...');
                pythonProcess.kill();
                pythonProcess = null;
            } else {
                console.log('brak procesu do zatrzymania.');
            }
        }

        if (ws === clients.stream) {
            handleStreamMessage(ws, data, isBinary);
        } else if (ws === clients.script) {
            handleScriptMessage(ws, data, isBinary);
        } else if (ws === clients.script2) {
            handleScriptMessage(ws, data, isBinary); // <--- dodane!
        } else if (ws.role === 'view') {
            // Dane od view.html -> do stream.html (raw frames)
            if (clients.stream && clients.stream.readyState === WebSocket.OPEN && !pythonProcess) {
                clients.stream.send(data, { binary: isBinary });
            }
        }
    });

    ws.on('close', () => {
        // Usuń klienta z odpowiedniej grupy
        if (ws.role === 'stream') {
            clients.stream = null;
            console.log('Klient stream rozłączony');
        } else if (ws.role === 'view') {
            clients.view = clients.view.filter(client => client !== ws);
            console.log('Klient view rozłączony');
        } else if (ws.role === 'script') {
            clients.script = null;
            console.log('Klient script rozłączony');
        } else if (ws.role === 'script2') {
            clients.script2 = null; // <--- usuń klienta script2
            console.log('Klient script2 rozłączony');
        } else if (ws.role === 'result') {
            clients.result = clients.result.filter(client => client !== ws);
            console.log('Klient result rozłączony');
        }
    });
});

// Nasłuchiwanie na porcie 8080
server.listen(8080, 'localhost', () => {
    console.log('Serwer HTTPS działa na https://localhost:8080');
});
