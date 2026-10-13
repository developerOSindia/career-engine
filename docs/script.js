// CareerOS Documentation Interactive Scripts

document.addEventListener('DOMContentLoaded', () => {
  // Tab Switching
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-tab');

      tabBtns.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const targetPane = document.getElementById(targetId);
      if (targetPane) {
        targetPane.classList.add('active');
      }
    });
  });

  // Copy to Clipboard with Toast
  const copyButtons = document.querySelectorAll('.copy-btn');
  const toast = document.getElementById('toast');

  copyButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const codeBlock = btn.closest('.code-box').querySelector('pre code');
      if (!codeBlock) return;

      const textToCopy = codeBlock.innerText.trim();

      navigator.clipboard.writeText(textToCopy).then(() => {
        showToast('Copied to clipboard! 📋');
        btn.innerHTML = '<span>Copied! ✓</span>';
        setTimeout(() => {
          btn.innerHTML = '<span>Copy</span>';
        }, 2000);
      }).catch(err => {
        console.error('Failed to copy:', err);
      });
    });
  });

  function showToast(message) {
    if (!toast) return;
    toast.innerText = message;
    toast.classList.add('show');
    setTimeout(() => {
      toast.classList.remove('show');
    }, 2500);
  }

  // Interactive Config Wizard Simulator
  const roleInput = document.getElementById('wizard-role');
  const expInput = document.getElementById('wizard-exp');
  const ctcInput = document.getElementById('wizard-ctc');
  const noticeInput = document.getElementById('wizard-notice');
  const previewBox = document.getElementById('wizard-preview');

  function updateConfigPreview() {
    if (!previewBox) return;
    const role = roleInput ? roleInput.value || 'Data Engineer' : 'Data Engineer';
    const exp = expInput ? expInput.value || '5' : '5';
    const ctc = ctcInput ? ctcInput.value || '30' : '30';
    const notice = noticeInput ? noticeInput.value || '30' : '30';

    const generated = {
      "candidate": {
        "full_name": "Your Name",
        "email": "you@example.com",
        "phone": "+91 9876543210",
        "location": "Bengaluru, India"
      },
      "professional_profile": {
        "primary_title": role,
        "total_experience_years": parseInt(exp, 10),
        "current_ctc_lpa": parseFloat(ctc),
        "expected_ctc_lpa": Math.round(parseFloat(ctc) * 1.3),
        "notice_period_days": parseInt(notice, 10),
        "preferred_work_mode": "Hybrid / Remote"
      },
      "custom_answers": {
        "Will you now or in the future require sponsorship?": "No",
        "Are you legally authorized to work in India?": "Yes"
      }
    };

    previewBox.textContent = JSON.stringify(generated, null, 2);
  }

  if (roleInput && expInput && ctcInput && noticeInput) {
    [roleInput, expInput, ctcInput, noticeInput].forEach(inp => {
      inp.addEventListener('input', updateConfigPreview);
    });
    updateConfigPreview();
  }
});
