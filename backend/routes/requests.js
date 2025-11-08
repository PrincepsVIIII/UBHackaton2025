const express = require('express');
const router = express.Router();
const { submitRequest, getRequests, updateRequestStatus } = require('../controllers/requestController');

router.post('/', submitRequest);
router.get('/', getRequests);
router.post('/:id/:action', updateRequestStatus);

module.exports = router;
