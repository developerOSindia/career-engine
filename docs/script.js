// CareerEngine by developerOS - Interactive Engine & 3D Visualization Scripts

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Three.js 3D Engine Visualization
  initThreeEngine();

  // Initialize Interactive Pipeline Simulation
  initPipelineTester();

  // Initialize 5-Role Resume Matcher Preview
  initResumeMatcherPreview();

  // Initialize 3D Card Tilt Effects
  initCard3DTilt();

  // Initialize FAQ Accordion
  initFaqAccordion();

  // Initialize Copy to Clipboard
  initCopyButtons();

  // Initialize Config Wizard Generator
  initConfigWizard();
});

/* ========================================================================= */
/* 1. THREE.JS 3D ENGINE VISUALIZATION (CYBERNETIC LOCAL CORE)               */
/* ========================================================================= */
function initThreeEngine() {
  const container = document.getElementById('three-canvas-container');
  const canvas = document.getElementById('three-engine-canvas');
  if (!container || !canvas || typeof THREE === 'undefined') return;

  const scene = new THREE.Scene();

  // Camera
  const camera = new THREE.PerspectiveCamera(
    45,
    container.clientWidth / container.clientHeight,
    0.1,
    1000
  );
  camera.position.z = 18;

  // Renderer
  const renderer = new THREE.WebGLRenderer({
    canvas: canvas,
    alpha: true,
    antialias: true
  });
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  // Lights
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
  scene.add(ambientLight);

  const pointLight1 = new THREE.PointLight(0xf97316, 2.5, 50); // developerOS Orange
  pointLight1.position.set(10, 10, 10);
  scene.add(pointLight1);

  const pointLight2 = new THREE.PointLight(0x06b6d4, 2.5, 50); // developerOS Cyan
  pointLight2.position.set(-10, -10, 10);
  scene.add(pointLight2);

  // Group for the entire Engine Core
  const engineGroup = new THREE.Group();
  scene.add(engineGroup);

  // 1. Central Icosahedron Wireframe Core
  const coreGeo = new THREE.IcosahedronGeometry(4, 2);
  const coreMat = new THREE.MeshStandardMaterial({
    color: 0x06b6d4,
    wireframe: true,
    transparent: true,
    opacity: 0.35,
    roughness: 0.2
  });
  const coreMesh = new THREE.Mesh(coreGeo, coreMat);
  engineGroup.add(coreMesh);

  // Inner Solid Polyhedron
  const innerGeo = new THREE.OctahedronGeometry(2.2, 0);
  const innerMat = new THREE.MeshStandardMaterial({
    color: 0xf97316,
    metalness: 0.8,
    roughness: 0.2,
    emissive: 0x78350f,
    emissiveIntensity: 0.4
  });
  const innerMesh = new THREE.Mesh(innerGeo, innerMat);
  engineGroup.add(innerMesh);

  // 2. Dual Orbiting Rings (CDP Stream & Gemini Loop)
  const ringGeo1 = new THREE.TorusGeometry(6.2, 0.05, 16, 100);
  const ringMat1 = new THREE.MeshBasicMaterial({
    color: 0xf97316,
    transparent: true,
    opacity: 0.65
  });
  const ring1 = new THREE.Mesh(ringGeo1, ringMat1);
  ring1.rotation.x = Math.PI / 3;
  engineGroup.add(ring1);

  const ringGeo2 = new THREE.TorusGeometry(7.2, 0.04, 16, 100);
  const ringMat2 = new THREE.MeshBasicMaterial({
    color: 0x06b6d4,
    transparent: true,
    opacity: 0.5
  });
  const ring2 = new THREE.Mesh(ringGeo2, ringMat2);
  ring2.rotation.y = Math.PI / 4;
  ring2.rotation.x = -Math.PI / 5;
  engineGroup.add(ring2);

  // 3. Floating Data Particles Constellation
  const particleCount = 180;
  const particleGeo = new THREE.BufferGeometry();
  const particlePositions = new Float32Array(particleCount * 3);
  const particleColors = new Float32Array(particleCount * 3);

  for (let i = 0; i < particleCount; i++) {
    const rad = 5 + Math.random() * 6;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);

    particlePositions[i * 3] = rad * Math.sin(phi) * Math.cos(theta);
    particlePositions[i * 3 + 1] = rad * Math.sin(phi) * Math.sin(theta);
    particlePositions[i * 3 + 2] = rad * Math.cos(phi);

    // Alternate cyan and orange
    if (i % 2 === 0) {
      particleColors[i * 3] = 0.98; // R
      particleColors[i * 3 + 1] = 0.45; // G (orange)
      particleColors[i * 3 + 2] = 0.09; // B
    } else {
      particleColors[i * 3] = 0.02; // R
      particleColors[i * 3 + 1] = 0.71; // G (cyan)
      particleColors[i * 3 + 2] = 0.83; // B
    }
  }

  particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
  particleGeo.setAttribute('color', new THREE.BufferAttribute(particleColors, 3));

  const particleMat = new THREE.PointsMaterial({
    size: 0.16,
    vertexColors: true,
    transparent: true,
    opacity: 0.85
  });

  const particleSystem = new THREE.Points(particleGeo, particleMat);
  engineGroup.add(particleSystem);

  // Interactive Mouse Control
  let mouseX = 0;
  let mouseY = 0;
  let targetRotationX = 0;
  let targetRotationY = 0;

  function onMouseMove(event) {
    const rect = container.getBoundingClientRect();
    const x = event.clientX - rect.left - rect.width / 2;
    const y = event.clientY - rect.top - rect.height / 2;
    mouseX = (x / rect.width) * 2;
    mouseY = (y / rect.height) * 2;
  }

  container.addEventListener('mousemove', onMouseMove);

  // Interactive View Modes (Engine Core, Packet Stream, Neural Flow)
  const tabBtns = document.querySelectorAll('.engine-tab-btn');
  let currentMode = 'core';

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentMode = btn.getAttribute('data-mode') || 'core';

      if (currentMode === 'packets') {
        camera.position.z = 14;
        coreMesh.material.opacity = 0.15;
        particleMat.size = 0.28;
      } else if (currentMode === 'neural') {
        camera.position.z = 22;
        coreMesh.material.opacity = 0.55;
        particleMat.size = 0.14;
      } else {
        camera.position.z = 18;
        coreMesh.material.opacity = 0.35;
        particleMat.size = 0.16;
      }
    });
  });

  // Render Loop
  let clock = new THREE.Clock();

  function animate() {
    requestAnimationFrame(animate);
    const delta = clock.getDelta();
    const time = clock.getElapsedTime();

    // Constant rotation
    coreMesh.rotation.y += 0.004;
    coreMesh.rotation.x += 0.002;
    innerMesh.rotation.y -= 0.01;
    innerMesh.rotation.z += 0.005;

    ring1.rotation.z += 0.008;
    ring2.rotation.z -= 0.006;
    particleSystem.rotation.y += 0.002;

    // Smooth mouse inertia
    targetRotationY += (mouseX * 0.8 - targetRotationY) * 0.05;
    targetRotationX += (mouseY * 0.8 - targetRotationX) * 0.05;

    engineGroup.rotation.y = targetRotationY + time * 0.05;
    engineGroup.rotation.x = targetRotationX;

    // Subtle pulsing scale
    const pulse = 1 + Math.sin(time * 2) * 0.02;
    innerMesh.scale.set(pulse, pulse, pulse);

    renderer.render(scene, camera);
  }

  animate();

  // Resize Listener
  window.addEventListener('resize', () => {
    if (!container) return;
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
  });
}

/* ========================================================================= */
/* 2. 4-STAGE PIPELINE TESTER SIMULATION                                      */
/* ========================================================================= */
function initPipelineTester() {
  const triggerBtn = document.getElementById('btn-run-simulation');
  const pulseBar = document.getElementById('tester-pulse-bar');
  const pulseFill = document.getElementById('tester-pulse-fill');
  const statusText = document.getElementById('tester-status-txt');
  const stepCards = document.querySelectorAll('.pipeline-step-card');

  if (!triggerBtn || !statusText || !stepCards.length) return;

  let isRunning = false;

  triggerBtn.addEventListener('click', () => {
    if (isRunning) return;
    isRunning = true;
    triggerBtn.disabled = true;
    triggerBtn.style.opacity = '0.6';
    if (pulseBar) pulseBar.style.display = 'block';

    const stages = [
      { step: 0, text: 'Stage 1/4: Chrome DevTools Protocol handshake on port 9222 (active session attached)...', progress: '25%' },
      { step: 1, text: 'Stage 2/4: Semantic resume selection matched profile "_SWE" for position target...', progress: '50%' },
      { step: 2, text: 'Stage 3/4: Gemini 2.5 Flash evaluated 4 screening questions in 380ms with 0 leaks...', progress: '75%' },
      { step: 3, text: 'Stage 4/4: Application recorded in jobs.db with SHA-256 deduplication (SUCCESS ✓)', progress: '100%' }
    ];

    let current = 0;

    function runNext() {
      // Clear previous active states
      stepCards.forEach(c => c.classList.remove('active-step'));

      if (current < stages.length) {
        const item = stages[current];
        stepCards[item.step].classList.add('active-step');
        statusText.textContent = item.text;
        statusText.style.color = '#67e8f9';
        if (pulseFill) pulseFill.style.width = item.progress;

        current++;
        setTimeout(runNext, 750);
      } else {
        statusText.textContent = 'Pipeline execution completed: 1 application submitted in Preview mode. Database synchronized.';
        statusText.style.color = '#22c55e';
        setTimeout(() => {
          stepCards.forEach(c => c.classList.remove('active-step'));
          triggerBtn.disabled = false;
          triggerBtn.style.opacity = '1';
          isRunning = false;
        }, 2000);
      }
    }

    runNext();
  });
}

/* ========================================================================= */
/* 3. 5-ROLE RESUME MATCHER PREVIEW INTERACTIVITY                            */
/* ========================================================================= */
function initResumeMatcherPreview() {
  const roleTags = document.querySelectorAll('.role-tag-item');
  const fileTarget = document.getElementById('preview-file-target');
  const keywordsContainer = document.getElementById('preview-keywords-cloud');
  const promptPreview = document.getElementById('preview-prompt-snippet');

  if (!roleTags.length || !fileTarget || !keywordsContainer || !promptPreview) return;

  const roleProfiles = {
    _DE: {
      filename: 'Candidate_Resume_DE.pdf',
      keywords: ['PySpark', 'Apache Airflow', 'Kafka', 'dbt', 'Snowflake', 'BigQuery', 'SQL Optimization', 'Delta Lake', 'ETL Pipelines'],
      prompt: 'ROLE_FOCUS: Data Engineering & Distributed Systems. Prioritize experience with data pipelines, orchestration (Airflow), big data throughput (Spark), and data warehouse modeling.'
    },
    _DS: {
      filename: 'Candidate_Resume_DS.pdf',
      keywords: ['Python', 'Pandas', 'Scikit-learn', 'A/B Testing', 'Hypothesis Testing', 'Statistical Modeling', 'Tableau', 'Feature Engineering'],
      prompt: 'ROLE_FOCUS: Data Science & Predictive Modeling. Emphasize causal inference, statistical experiment design, business metrics analysis, and machine learning model validation.'
    },
    _AI: {
      filename: 'Candidate_Resume_AI.pdf',
      keywords: ['LLMs', 'RAG Pipelines', 'LangChain', 'Vector DBs', 'Gemini API', 'Fine-Tuning', 'LlamaIndex', 'Prompt Architecture', 'PyTorch'],
      prompt: 'ROLE_FOCUS: Artificial Intelligence & Generative AI. Highlight LLM orchestration, embedding indexes, semantic search accuracy, and agentic tool-use architecture.'
    },
    _SWE: {
      filename: 'Candidate_Resume_SWE.pdf',
      keywords: ['TypeScript', 'Python', 'React', 'Node.js', 'System Architecture', 'PostgreSQL', 'Docker', 'RESTful APIs', 'Microservices'],
      prompt: 'ROLE_FOCUS: Full-Stack & Software Engineering. Emphasize scalable backend services, API design, robust TypeScript client architecture, and distributed systems resilience.'
    },
    _MLOps: {
      filename: 'Candidate_Resume_MLOps.pdf',
      keywords: ['Kubeflow', 'MLflow', 'Docker', 'Kubernetes', 'Triton Server', 'Model Monitoring', 'CI/CD Pipelines', 'AWS SageMaker', 'Drift Detection'],
      prompt: 'ROLE_FOCUS: Machine Learning Operations & Infrastructure. Highlight low-latency inference serving, container orchestration, automated model retraining, and telemetry monitoring.'
    }
  };

  roleTags.forEach(tag => {
    tag.addEventListener('click', (e) => {
      e.preventDefault();
      roleTags.forEach(t => t.classList.remove('active'));
      tag.classList.add('active');

      const roleId = tag.getAttribute('data-role');
      const data = roleProfiles[roleId];
      if (!data) return;

      fileTarget.textContent = data.filename;
      promptPreview.textContent = data.prompt;

      // Render keywords
      keywordsContainer.innerHTML = '';
      data.keywords.forEach(kw => {
        const span = document.createElement('span');
        span.className = 'kw-chip';
        span.textContent = kw;
        keywordsContainer.appendChild(span);
      });
    });
  });
}

/* ========================================================================= */
/* 4. 3D CARD TILT EFFECT                                                    */
/* ========================================================================= */
function initCard3DTilt() {
  const cards = document.querySelectorAll('.tilt-card');
  if (!cards.length) return;

  cards.forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const centerX = rect.width / 2;
      const centerY = rect.height / 2;

      const rotateX = ((y - centerY) / centerY) * -6;
      const rotateY = ((x - centerX) / centerX) * 6;

      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.01, 1.01, 1.01)`;
    });

    card.addEventListener('mouseleave', () => {
      card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
    });
  });
}

/* ========================================================================= */
/* 5. FAQ ACCORDION                                                          */
/* ========================================================================= */
function initFaqAccordion() {
  const faqItems = document.querySelectorAll('.faq-item');
  faqItems.forEach(item => {
    const question = item.querySelector('.faq-question');
    if (!question) return;
    question.addEventListener('click', () => {
      const isOpen = item.classList.contains('open');
      faqItems.forEach(i => i.classList.remove('open'));
      if (!isOpen) {
        item.classList.add('open');
      }
    });
  });
}

/* ========================================================================= */
/* 6. COPY BUTTONS WITH TOAST                                                */
/* ========================================================================= */
function initCopyButtons() {
  const copyButtons = document.querySelectorAll('.copy-btn');
  const toast = document.getElementById('toast');

  copyButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const codeBlock = btn.closest('.code-box, .terminal-box')?.querySelector('pre code, pre');
      if (!codeBlock) return;

      const text = codeBlock.innerText.replace(/^\$\s+/gm, '').trim();
      navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard! 📋');
        const origText = btn.innerHTML;
        btn.innerHTML = '<span>Copied! ✓</span>';
        setTimeout(() => {
          btn.innerHTML = origText;
        }, 2000);
      }).catch(err => {
        console.error('Copy failed:', err);
      });
    });
  });

  function showToast(msg) {
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => {
      toast.classList.remove('show');
    }, 2400);
  }
}

/* ========================================================================= */
/* 7. CONFIG WIZARD LIVE PREVIEW                                             */
/* ========================================================================= */
function initConfigWizard() {
  const roleInput = document.getElementById('wizard-role');
  const expInput = document.getElementById('wizard-exp');
  const ctcInput = document.getElementById('wizard-ctc');
  const noticeInput = document.getElementById('wizard-notice');
  const previewBox = document.getElementById('wizard-preview');

  if (!roleInput || !previewBox) return;

  function update() {
    const role = roleInput.value || 'Data Engineer';
    const exp = parseInt(expInput?.value || '5', 10);
    const ctc = parseFloat(ctcInput?.value || '30');
    const notice = parseInt(noticeInput?.value || '30', 10);

    const config = {
      candidate: {
        full_name: "Your Name",
        email: "you@example.com",
        phone: "+91 9876543210",
        location: "Bengaluru, India"
      },
      professional_profile: {
        primary_title: role,
        total_experience_years: exp,
        current_ctc_lpa: ctc,
        expected_ctc_lpa: Math.round(ctc * 1.3),
        notice_period_days: notice,
        preferred_work_mode: "Hybrid / Remote"
      },
      custom_answers: {
        "Will you now or in the future require sponsorship?": "No",
        "Are you legally authorized to work in India?": "Yes"
      }
    };

    previewBox.textContent = JSON.stringify(config, null, 2);
  }

  [roleInput, expInput, ctcInput, noticeInput].forEach(inp => {
    if (inp) inp.addEventListener('input', update);
  });

  update();
}
