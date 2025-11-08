const { Request } = require('../models');
const axios = require('axios');

exports.submitRequest = async (req, res) => {
  const { address, description } = req.body;

  try {
    const response = await axios.get(`https://maps.googleapis.com/maps/api/geocode/json`, {
      params: { address, key: process.env.GOOGLE_MAPS_API_KEY }
    });

    if (response.data.status !== "OK") return res.status(400).json({ message: "Invalid address" });

    const request = await Request.create({ address, description });
    res.json(request);
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "Server error" });
  }
};

exports.getRequests = async (req, res) => {
  try {
    const requests = await Request.findAll({ order: [['createdAt', 'DESC']] });
    res.json(requests);
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "Server error" });
  }
};

exports.updateRequestStatus = async (req, res) => {
  const { id, action } = req.params;
  if (!['accept', 'decline'].includes(action)) return res.status(400).json({ message: "Invalid action" });

  try {
    const request = await Request.findByPk(id);
    if (!request) return res.status(404).json({ message: "Request not found" });

    request.status = action === 'accept' ? 'accepted' : 'declined';
    await request.save();
    res.json(request);
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "Server error" });
  }
};
