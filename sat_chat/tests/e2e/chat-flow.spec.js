/**
 * E2E Test - Complete Chat Flow
 * 사용자 관점에서 전체 채팅 플로우를 테스트합니다
 */

const { test, expect } = require('@playwright/test');

test.describe('SAT Chat - 전체 사용자 플로우', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
  });

  test('신규 사용자 가입 및 첫 메시지 전송', async ({ page }) => {
    // 1. 회원가입 페이지로 이동
    await page.click('text=Sign Up');
    
    // 2. 회원가입 폼 작성
    await page.fill('input[name="username"]', 'testuser123');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'SecurePass123!');
    await page.fill('input[name="confirmPassword"]', 'SecurePass123!');
    
    // 3. 가입 버튼 클릭
    await page.click('button[type="submit"]');
    
    // 4. 대시보드로 리다이렉트 확인
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('text=Welcome, testuser123')).toBeVisible();
    
    // 5. 채팅방 생성
    await page.click('button:has-text("New Chat")');
    await page.fill('input[name="roomName"]', 'My First Chat Room');
    await page.click('button:has-text("Create Room")');
    
    // 6. 채팅방 입장 확인
    await expect(page.locator('h2:has-text("My First Chat Room")')).toBeVisible();
    
    // 7. 첫 메시지 전송
    await page.fill('textarea[placeholder="Type a message..."]', 'Hello World!');
    await page.press('textarea[placeholder="Type a message..."]', 'Enter');
    
    // 8. 메시지 표시 확인
    const message = page.locator('.message-content:has-text("Hello World!")');
    await expect(message).toBeVisible();
  });

  test('실시간 메시지 송수신', async ({ browser }) => {
    // 두 개의 브라우저 컨텍스트 생성 (두 명의 사용자)
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();
    
    // 사용자 1 로그인
    await page1.goto('http://localhost:3000/login');
    await page1.fill('input[name="email"]', 'user1@example.com');
    await page1.fill('input[name="password"]', 'Password123!');
    await page1.click('button[type="submit"]');
    
    // 사용자 2 로그인
    await page2.goto('http://localhost:3000/login');
    await page2.fill('input[name="email"]', 'user2@example.com');
    await page2.fill('input[name="password"]', 'Password123!');
    await page2.click('button[type="submit"]');
    
    // 같은 채팅방 입장
    const chatRoomId = 'general';
    await page1.goto(`http://localhost:3000/chat/${chatRoomId}`);
    await page2.goto(`http://localhost:3000/chat/${chatRoomId}`);
    
    // 사용자 1이 메시지 전송
    await page1.fill('textarea[placeholder="Type a message..."]', 'Hello from User 1!');
    await page1.press('textarea[placeholder="Type a message..."]', 'Enter');
    
    // 사용자 2 화면에서 메시지 확인
    const messageOnPage2 = page2.locator('.message-content:has-text("Hello from User 1!")');
    await expect(messageOnPage2).toBeVisible({ timeout: 5000 });
    
    // 사용자 2가 답장
    await page2.fill('textarea[placeholder="Type a message..."]', 'Hi User 1! Nice to meet you!');
    await page2.press('textarea[placeholder="Type a message..."]', 'Enter');
    
    // 사용자 1 화면에서 답장 확인
    const replyOnPage1 = page1.locator('.message-content:has-text("Hi User 1! Nice to meet you!")');
    await expect(replyOnPage1).toBeVisible({ timeout: 5000 });
    
    await context1.close();
    await context2.close();
  });

  test('타이핑 인디케이터 표시', async ({ browser }) => {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();
    
    // 두 사용자 로그인 및 같은 방 입장
    await loginUser(page1, 'user1@example.com', 'Password123!');
    await loginUser(page2, 'user2@example.com', 'Password123!');
    
    await page1.goto('http://localhost:3000/chat/general');
    await page2.goto('http://localhost:3000/chat/general');
    
    // 사용자 1이 타이핑 시작
    await page1.fill('textarea[placeholder="Type a message..."]', 'I am typing...');
    
    // 사용자 2 화면에서 타이핑 인디케이터 확인
    const typingIndicator = page2.locator('.typing-indicator:has-text("user1 is typing")');
    await expect(typingIndicator).toBeVisible();
    
    // 사용자 1이 메시지 전송
    await page1.press('textarea[placeholder="Type a message..."]', 'Enter');
    
    // 타이핑 인디케이터 사라짐 확인
    await expect(typingIndicator).not.toBeVisible();
    
    await context1.close();
    await context2.close();
  });

  test('파일 업로드 및 미리보기', async ({ page }) => {
    // 로그인
    await loginUser(page, 'test@example.com', 'Password123!');
    
    // 채팅방 입장
    await page.goto('http://localhost:3000/chat/general');
    
    // 파일 업로드 버튼 클릭
    await page.click('button[aria-label="Attach file"]');
    
    // 파일 선택
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('tests/fixtures/test-image.jpg');
    
    // 미리보기 확인
    await expect(page.locator('.file-preview img')).toBeVisible();
    
    // 전송 버튼 클릭
    await page.click('button:has-text("Send")');
    
    // 메시지에 이미지 표시 확인
    await expect(page.locator('.message-attachment img')).toBeVisible();
    
    // 이미지 클릭하여 확대 보기
    await page.click('.message-attachment img');
    await expect(page.locator('.image-modal')).toBeVisible();
    
    // 모달 닫기
    await page.press('body', 'Escape');
    await expect(page.locator('.image-modal')).not.toBeVisible();
  });

  test('메시지 검색 기능', async ({ page }) => {
    await loginUser(page, 'test@example.com', 'Password123!');
    await page.goto('http://localhost:3000/chat/general');
    
    // 검색 버튼 클릭
    await page.click('button[aria-label="Search messages"]');
    
    // 검색어 입력
    await page.fill('input[placeholder="Search messages..."]', 'important');
    await page.press('input[placeholder="Search messages..."]', 'Enter');
    
    // 검색 결과 확인
    const searchResults = page.locator('.search-results');
    await expect(searchResults).toBeVisible();
    
    // 검색 결과 개수 확인
    const resultCount = await page.locator('.search-result-item').count();
    expect(resultCount).toBeGreaterThan(0);
    
    // 검색 결과 클릭하여 해당 메시지로 이동
    await page.click('.search-result-item:first-child');
    
    // 메시지 하이라이트 확인
    await expect(page.locator('.message.highlighted')).toBeVisible();
  });

  test('이모지 반응 추가', async ({ page }) => {
    await loginUser(page, 'test@example.com', 'Password123!');
    await page.goto('http://localhost:3000/chat/general');
    
    // 메시지에 호버
    const message = page.locator('.message-content').first();
    await message.hover();
    
    // 반응 버튼 클릭
    await page.click('button[aria-label="Add reaction"]');
    
    // 이모지 선택
    await page.click('.emoji-picker button:has-text("👍")');
    
    // 반응 표시 확인
    await expect(page.locator('.message-reactions:has-text("👍")')).toBeVisible();
    
    // 반응 개수 확인
    const reactionCount = page.locator('.reaction-count:has-text("1")');
    await expect(reactionCount).toBeVisible();
  });

  test('메시지 수정 및 삭제', async ({ page }) => {
    await loginUser(page, 'test@example.com', 'Password123!');
    await page.goto('http://localhost:3000/chat/general');
    
    // 메시지 전송
    await page.fill('textarea[placeholder="Type a message..."]', 'Original message');
    await page.press('textarea[placeholder="Type a message..."]', 'Enter');
    
    // 메시지 옵션 메뉴 열기
    const message = page.locator('.message-content:has-text("Original message")');
    await message.hover();
    await page.click('button[aria-label="Message options"]');
    
    // 수정 옵션 선택
    await page.click('text=Edit');
    
    // 메시지 수정
    await page.fill('.message-edit-input', 'Edited message');
    await page.press('.message-edit-input', 'Enter');
    
    // 수정된 메시지 확인
    await expect(page.locator('.message-content:has-text("Edited message")')).toBeVisible();
    await expect(page.locator('.message-edited-label')).toBeVisible();
    
    // 메시지 삭제
    await message.hover();
    await page.click('button[aria-label="Message options"]');
    await page.click('text=Delete');
    
    // 확인 다이얼로그
    await page.click('button:has-text("Confirm Delete")');
    
    // 메시지 삭제 확인
    await expect(page.locator('.message-content:has-text("Edited message")')).not.toBeVisible();
  });

  test('알림 설정 변경', async ({ page }) => {
    await loginUser(page, 'test@example.com', 'Password123!');
    
    // 설정 페이지로 이동
    await page.goto('http://localhost:3000/settings/notifications');
    
    // 알림 토글 확인
    const desktopNotifications = page.locator('input[name="desktopNotifications"]');
    const soundNotifications = page.locator('input[name="soundNotifications"]');
    
    // 데스크톱 알림 활성화
    await desktopNotifications.check();
    await expect(desktopNotifications).toBeChecked();
    
    // 소리 알림 비활성화
    await soundNotifications.uncheck();
    await expect(soundNotifications).not.toBeChecked();
    
    // 설정 저장
    await page.click('button:has-text("Save Settings")');
    
    // 성공 메시지 확인
    await expect(page.locator('.toast-success:has-text("Settings saved")')).toBeVisible();
  });

  test('다크 모드 전환', async ({ page }) => {
    await loginUser(page, 'test@example.com', 'Password123!');
    
    // 초기 라이트 모드 확인
    await expect(page.locator('body')).not.toHaveClass(/dark-mode/);
    
    // 다크 모드 토글 클릭
    await page.click('button[aria-label="Toggle dark mode"]');
    
    // 다크 모드 적용 확인
    await expect(page.locator('body')).toHaveClass(/dark-mode/);
    
    // 페이지 새로고침 후에도 유지되는지 확인
    await page.reload();
    await expect(page.locator('body')).toHaveClass(/dark-mode/);
  });
});

// Helper function for login
async function loginUser(page, email, password) {
  await page.goto('http://localhost:3000/login');
  await page.fill('input[name="email"]', email);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL('/dashboard');
}