use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use warp::Filter;
use futures_util::{StreamExt, SinkExt};
use tracing::{info, warn, error};
use warp::ws::{Message, WebSocket};
use serde::{Deserialize, Serialize};
use sqlx::postgres::{PgPoolOptions, PgListener};

type PeerMap = Arc<RwLock<HashMap<String, tokio::sync::mpsc::UnboundedSender<Result<Message, warp::Error>>>>>;

#[derive(Deserialize, Serialize, Debug)]
struct Envelope {
    sender_public_key: String,
    target_public_key: String,
    encrypted_payload: String,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt::init();
    info!("🚀 Booting OpenConnect Rust Relay Server...");

    // 1. Connect to PostgreSQL
    let database_url = std::env::var("DATABASE_URL")
        .unwrap_or_else(|_| "postgres://oc_admin:oc_password@127.0.0.1:5432/openconnect".to_string());
    
    info!("Connecting to PostgreSQL database...");
    let pool = PgPoolOptions::new()
        .max_connections(5)
        .connect(&database_url)
        .await?;
    info!("✅ Connected to Database.");

    let connected_peers: PeerMap = Arc::new(RwLock::new(HashMap::new()));

    // 2. Start the PostgreSQL Listener in the background
    let peers_for_db = connected_peers.clone();
    let db_url_clone = database_url.clone();
    tokio::spawn(async move {
        listen_for_db_events(&db_url_clone, peers_for_db).await;
    });

    // 3. Setup WebSocket Routes
    let ws_route = warp::path("ws")
        .and(warp::path::param())
        .and(warp::ws())
        .and(with_peers(connected_peers.clone()))
        .map(|device_pub_key: String, ws: warp::ws::Ws, peers| {
            ws.on_upgrade(move |socket| handle_client(device_pub_key, socket, peers))
        });

    let health_route = warp::path!("health").map(|| warp::reply::html("OK"));
    let routes = health_route.or(ws_route);

    info!("Listening on 0.0.0.0:9000");
    warp::serve(routes).run(([0, 0, 0, 0], 9000)).await;
    
    Ok(())
}

async fn listen_for_db_events(database_url: &str, peers: PeerMap) {
    let mut listener = PgListener::connect(database_url).await.expect("Failed to create PG Listener");
    
    // Listen to the specific channel we will tell Django to broadcast on
    listener.listen("subscription_events").await.expect("Failed to listen to channel");
    info!("👂 Listening for PostgreSQL 'subscription_events' from Django...");

    loop {
        match listener.recv().await {
            Ok(notification) => {
                let payload = notification.payload();
                info!("🔔 Received DB Event: {}", payload);
                
                // Expected format from Django: "CANCELLED:target_public_key"
                if payload.starts_with("CANCELLED:") {
                    let parts: Vec<&str> = payload.split(':').collect();
                    if parts.len() == 2 {
                        let target_key = parts[1];
                        info!("💀 User Subscription Expired. Forcing disconnect for device: {}", target_key);
                        
                        // Physically sever the WebSocket connection!
                        peers.write().await.remove(target_key);
                    }
                }
            },
            Err(e) => {
                error!("Database listener error: {}", e);
                tokio::time::sleep(std::time::Duration::from_secs(2)).await;
            }
        }
    }
}

fn with_peers(peers: PeerMap) -> impl Filter<Extract = (PeerMap,), Error = std::convert::Infallible> + Clone {
    warp::any().map(move || peers.clone())
}

async fn handle_client(device_pub_key: String, ws: WebSocket, peers: PeerMap) {
    info!("🔗 Device Connected: {}", device_pub_key);

    let (mut client_ws_sender, mut client_ws_rcv) = ws.split();
    let (tx, mut rx) = tokio::sync::mpsc::unbounded_channel();

    peers.write().await.insert(device_pub_key.clone(), tx);

    tokio::task::spawn(async move {
        while let Some(message) = rx.recv().await {
            client_ws_sender
                .send(message.unwrap_or(Message::close()))
                .await
                .unwrap_or_else(|e| {
                    error!("WebSocket send error: {}", e);
                });
        }
    });

    while let Some(result) = client_ws_rcv.next().await {
        let msg = match result {
            Ok(msg) => msg,
            Err(_) => break,
        };

        if let Ok(text) = msg.to_str() {
            if let Ok(envelope) = serde_json::from_str::<Envelope>(text) {
                let peers_lock = peers.read().await;
                if let Some(target_tx) = peers_lock.get(&envelope.target_public_key) {
                    let _ = target_tx.send(Ok(Message::text(text)));
                }
            }
        }
    }

    info!("❌ Device Disconnected: {}", device_pub_key);
    peers.write().await.remove(&device_pub_key);
}