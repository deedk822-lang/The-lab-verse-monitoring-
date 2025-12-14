import sqlite3 from 'sqlite3';
import { open } from 'sqlite';

export default async function handler(req, res) {
  try {
    const db = await open({
      filename: './data/vaal_empire.db',
      driver: sqlite3.Database
    });

    const clients = await db.all('SELECT * FROM clients');
    const revenue = await db.all('SELECT * FROM revenue');

    res.status(200).json({ clients, revenue });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}
