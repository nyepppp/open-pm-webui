/**
 * Offline sync service
 * Manages local cache and background synchronization
 */

import type { CanvasState } from '$lib/types/canvas';

const DB_NAME = 'CanvasOfflineDB';
const DB_VERSION = 1;
const STORE_NAME = 'canvas-cache';

interface SyncQueueItem {
  id: string;
  canvasId: string;
  operation: 'create' | 'update' | 'delete';
  data: unknown;
  timestamp: number;
}

class OfflineSyncService {
  private db: IDBDatabase | null = null;
  private syncQueue: SyncQueueItem[] = [];
  private isOnline = navigator.onLine;

  constructor() {
    this.initDB();
    this.setupEventListeners();
  }

  private async initDB(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          db.createObjectStore(STORE_NAME, { keyPath: 'id' });
        }
      };
    });
  }

  private setupEventListeners(): void {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.sync();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
    });
  }

  async saveCanvas(canvas: CanvasState): Promise<void> {
    await this.ensureDB();
    
    const transaction = this.db!.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    
    return new Promise((resolve, reject) => {
      const request = store.put({
        id: canvas.id,
        data: JSON.stringify(canvas),
        timestamp: Date.now()
      });
      
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async loadCanvas(canvasId: string): Promise<CanvasState | null> {
    await this.ensureDB();
    
    const transaction = this.db!.transaction([STORE_NAME], 'readonly');
    const store = transaction.objectStore(STORE_NAME);
    
    return new Promise((resolve, reject) => {
      const request = store.get(canvasId);
      
      request.onsuccess = () => {
        if (request.result) {
          resolve(JSON.parse(request.result.data));
        } else {
          resolve(null);
        }
      };
      
      request.onerror = () => reject(request.error);
    });
  }

  async deleteCanvas(canvasId: string): Promise<void> {
    await this.ensureDB();
    
    const transaction = this.db!.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    
    return new Promise((resolve, reject) => {
      const request = store.delete(canvasId);
      
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async queueSync(item: SyncQueueItem): Promise<void> {
    this.syncQueue.push(item);
    
    if (this.isOnline) {
      await this.sync();
    }
  }

  async sync(): Promise<void> {
    if (!this.isOnline || this.syncQueue.length === 0) return;

    const itemsToSync = [...this.syncQueue];
    this.syncQueue = [];

    for (const item of itemsToSync) {
      try {
        // Attempt to sync with backend
        await this.syncItem(item);
      } catch (error) {
        // If sync fails, re-queue the item
        this.syncQueue.push(item);
      }
    }
  }

  private async syncItem(item: SyncQueueItem): Promise<void> {
    // Implementation would call the actual API
    // This is a placeholder for the sync logic
    console.log('Syncing item:', item);
  }

  private async ensureDB(): Promise<void> {
    if (!this.db) {
      await this.initDB();
    }
  }
}

export const offlineSync = new OfflineSyncService();
