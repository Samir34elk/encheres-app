export const DATABASE_CONFIG = {
  url: process.env.DATABASE_URL || 'postgresql://localhost:5432/encheres',
  pool: {
    min: 2,
    max: 10
  },
  debug: process.env.NODE_ENV !== 'production'
};
