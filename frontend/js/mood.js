/**
 * MindCare AI — Mood Tracker Module
 * Handles mood emoji selection and logging to the API
 */

const MoodTracker = (() => {
  let selectedScore = null;

  function init() {
    const buttons = document.querySelectorAll('.mood-btn');
    const noteArea = document.getElementById('moodNoteArea');
    const logBtn = document.getElementById('logMoodBtn');
    const feedback = document.getElementById('moodFeedback');

    if (!buttons.length) return;

    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        buttons.forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        selectedScore = parseInt(btn.dataset.score, 10);
        if (noteArea) noteArea.style.display = 'flex';
      });
    });

    if (logBtn) {
      logBtn.addEventListener('click', async () => {
        if (!selectedScore) return;
        const note = document.getElementById('moodNote')?.value || '';
        const sessionId = window.mindcareSession?.sessionId;

        if (!sessionId) {
          if (feedback) feedback.textContent = 'Start a conversation first!';
          return;
        }

        try {
          const res = await fetch('/api/mood', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              session_id: sessionId,
              mood_score: selectedScore,
              note: note || null
            })
          });

          if (res.ok) {
            if (feedback) {
              feedback.textContent = '✓ Mood logged!';
              setTimeout(() => { feedback.textContent = ''; }, 3000);
            }
            if (noteArea) noteArea.style.display = 'none';
            document.getElementById('moodNote').value = '';
            buttons.forEach(b => b.classList.remove('selected'));
            selectedScore = null;
          }
        } catch (err) {
          if (feedback) feedback.textContent = 'Could not log mood.';
        }
      });
    }
  }

  return { init };
})();

document.addEventListener('DOMContentLoaded', MoodTracker.init);
