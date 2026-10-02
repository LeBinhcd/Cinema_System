/* Read-only chat UI. Untrusted content is always rendered as text, never HTML. */
(() => {
  'use strict';
  const root = document.getElementById('cinema-chat');
  if (!root) return;
  const toggle = document.getElementById('chat-toggle');
  const panel = document.getElementById('chat-panel');
  const close = document.getElementById('chat-close');
  const history = document.getElementById('chat-history');
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-question');
  const send = document.getElementById('chat-send');
  const count = document.getElementById('chat-count');
  const validation = document.getElementById('chat-validation');
  const loading = document.getElementById('chat-loading');
  let busy = false;

  const scroll = () => { history.scrollTop = history.scrollHeight; };
  const text = (tag, value, className) => {
    const element = document.createElement(tag);
    element.textContent = value;
    if (className) element.className = className;
    return element;
  };
  const message = (value, kind) => {
    const node = text('div', value, `cinema-chat__message cinema-chat__message--${kind}`);
    history.append(node);
    scroll();
    return node;
  };
  const setOpen = (open) => {
    panel.hidden = !open;
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Thu nhỏ trợ lý điện ảnh' : 'Mở trợ lý điện ảnh');
    if (open) { input.focus(); scroll(); } else toggle.focus();
  };
  toggle.hidden = false;
  toggle.addEventListener('click', () => setOpen(panel.hidden));
  close.addEventListener('click', () => setOpen(false));
  root.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !panel.hidden) setOpen(false);
  });
  input.addEventListener('input', () => {
    count.textContent = `${Array.from(input.value).length}/300`;
    validation.textContent = '';
  });

  const renderCard = (card) => {
    if (!card || !Number.isSafeInteger(card.screening_id) || card.screening_id <= 0 ||
        typeof card.movie_title !== 'string' || typeof card.room_name !== 'string' ||
        typeof card.start_time !== 'string') return;
    const seats = card.seats_available;
    const types = ['STANDARD', 'VIP', 'COUPLE'];
    if (!seats || !types.every((type) => Number.isSafeInteger(seats[type]) && seats[type] >= 0)) return;
    const node = document.createElement('article');
    node.className = 'cinema-chat__card';
    node.append(text('h3', card.movie_title));
    // Keep the backend's local cinema time; do not let the browser change timezone.
    node.append(text('p', `Giờ chiếu: ${card.start_time.replace('T', ' ')}`));
    node.append(text('p', `Phòng: ${card.room_name}`));
    node.append(text('p', `Standard: ${seats.STANDARD} · VIP: ${seats.VIP} · Couple: ${seats.COUPLE}`));
    const expectedUrl = `/booking/${card.screening_id}`;
    if (card.booking_url === expectedUrl && card.sales_open !== false && types.some((type) => seats[type] > 0)) {
      const link = text('a', 'Đặt vé ngay', 'cinema-chat__booking');
      link.setAttribute('href', expectedUrl);
      node.append(link);
    } else {
      node.append(text('p', 'Hiện chưa thể đặt vé cho suất chiếu này.'));
    }
    history.append(node);
  };

  const requestAnswer = async (question, retryNode = null) => {
    if (busy) return;
    busy = true;
    send.disabled = true;
    loading.hidden = false;
    history.setAttribute('aria-busy', 'true');
    root.querySelectorAll('.cinema-chat__retry').forEach((button) => { button.disabled = true; });
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 20000);
    try {
      const token = document.querySelector('meta[name="csrf-token"]')?.content;
      if (!token) throw new Error('csrf');
      const response = await fetch('/api/chat', {
        method: 'POST', credentials: 'same-origin', signal: controller.signal,
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': token },
        body: JSON.stringify({ question })
      });
      if (!response.ok) throw new Error(response.status === 403 ? 'csrf' : 'http');
      const data = await response.json();
      if (!data || typeof data.answer !== 'string' || !data.answer.trim() || !Array.isArray(data.cards)) {
        throw new Error('invalid-response');
      }
      if (retryNode) retryNode.remove();
      message(data.answer, 'assistant');
      data.cards.forEach(renderCard);
    } catch (error) {
      if (retryNode) retryNode.remove();
      const csrfError = error.message === 'csrf';
      const node = message(csrfError
        ? 'Phiên làm việc đã thay đổi. Vui lòng tải lại trang rồi gửi câu hỏi.'
        : 'Xin lỗi, chưa thể kết nối với trợ lý. Bạn có thể thử lại.', 'error');
      if (!csrfError) {
        const retry = text('button', 'Thử lại', 'cinema-chat__retry');
        retry.type = 'button';
        retry.addEventListener('click', () => requestAnswer(question, node));
        node.append(document.createElement('br'), retry);
      }
    } finally {
      window.clearTimeout(timeout);
      busy = false;
      send.disabled = false;
      loading.hidden = true;
      history.setAttribute('aria-busy', 'false');
      root.querySelectorAll('.cinema-chat__retry').forEach((button) => { button.disabled = false; });
      scroll();
    }
  };

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    if (busy) return;
    const question = input.value.trim();
    if (!question || Array.from(input.value).length > 300) {
      validation.textContent = !question ? 'Vui lòng nhập câu hỏi.' : 'Tối đa 300 ký tự; vui lòng rút gọn câu hỏi.';
      input.focus();
      return;
    }
    validation.textContent = '';
    message(question, 'user');
    input.value = '';
    count.textContent = '0/300';
    requestAnswer(question);
  });
  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      form.requestSubmit();
    }
  });
})();