-- Checkpoints saved for one conversation; replace the sample chat_id.
SELECT thread_id, checkpoint_id
FROM checkpoints
WHERE thread_id = 'demo-thread';
