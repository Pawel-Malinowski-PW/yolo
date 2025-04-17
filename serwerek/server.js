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
    stream: null, // Klient wysyłający dane z kamery (stream.html)
    view: [],     // Klienci odbierający oryginalne dane (view.html)
    script: null, // Klient przetwarzający dane (script.py)
    result: []    // Klienci odbierający przetworzone dane (result.html)
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
            } else if (role === 'result') {
                clients.result.push(ws);
                console.log('Klient result połączony');
            } else {
                console.error(`Nieznana rola klienta: ${role}`);
            }
            return;
        }

        if (data.toString() === 'start-script') {
            console.log('Włączanie script.py...');
            pythonProcess = spawn('python', ['script.py'], {
                cwd: __dirname, // upewnij się, że skrypt jest w tym samym katalogu
            });

            pythonProcess.stdout.on('data', (data) => {
                console.log(`script.py stdout: ${data}`);
            });

            pythonProcess.stderr.on('data', (data) => {
                console.error(`script.py stderr: ${data}`);
            });

            pythonProcess.on('close', (code) => {
                console.log(`script.py zakończył prace z kodem ${code}`);
                pythonProcess = null; // zresetuj proces po zakończeniu
            });
        } else if (data.toString() === 'stop-script') {
            if (pythonProcess) {
                console.log('Zatrzymywanie script.py...');
                pythonProcess.kill(); // zabicie procesu
                pythonProcess = null;
            } else {
                console.log('brak procesu do zatrzymania.');
            }
        }

        if (ws === clients.stream) {
            handleStreamMessage(ws, data, isBinary);
        } else if (ws === clients.script) {
            handleScriptMessage(ws, data, isBinary);
        } else if (ws.role === 'view') {
            // Dane od view.html -> do stream.html (raw frames)
            if (clients.stream && clients.stream.readyState === WebSocket.OPEN && !pythonProcess) {
                clients.stream.send(data, { binary: isBinary });
            }
        }
    });

    ws.on('close', () => {
        console.log('WebSocket rozłączony');
        // Usuń klienta z odpowiedniej grupy
        if (ws.role === 'stream') {
            clients.stream = null;
        } else if (ws.role === 'view') {
            clients.view = clients.view.filter(client => client !== ws);
        } else if (ws.role === 'script') {
            clients.script = null;
        } else if (ws.role === 'result') {
            clients.result = clients.result.filter(client => client !== ws);
        }
    });
});

// Nasłuchiwanie na porcie 8080
server.listen(8080, '172.29.192.121', () => {
    console.log('Serwer HTTPS działa na https://172.29.192.121:8080');
});
