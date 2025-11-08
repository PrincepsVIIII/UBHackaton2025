const { DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  const Request = sequelize.define('Request', {
    address: DataTypes.STRING,
    description: DataTypes.TEXT,
    status: { type: DataTypes.STRING, defaultValue: 'pending' }
  });

  return Request;
};
