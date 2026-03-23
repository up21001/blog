---
title: "Flutter 3.x로 iOS/Android 동시 개발 — 13년 차 엔지니어의 실전 입문기"
date: 2026-03-23T22:30:00+09:00
lastmod: 2026-03-23T22:30:00+09:00
description: "하드웨어·백엔드 위주였던 13년 차 엔지니어가 Flutter 3.x로 크로스플랫폼 앱을 처음 만들면서 겪은 실전 경험. Dart 언어 적응, 상태관리, 배포까지 솔직한 후기."
slug: "flutter-crossplatform-practical-guide"
categories: ["software-dev"]
tags: ["Flutter", "Dart", "크로스플랫폼", "iOS", "Android"]
series: []
draft: false
---

솔직히 말하면 Flutter를 오랫동안 외면했습니다. "Dart라는 언어를 또 배워야 해?"라는 거부감이 있었습니다. Python, C/C++, JavaScript를 쓰던 입장에서 굳이 Dart를 배워야 하나 싶었거든요.

그런데 클라이언트에서 iOS/Android 앱을 같이 만들어달라는 요청이 왔을 때 선택지를 비교해봤습니다. React Native는 JavaScript라 친숙하지만 네이티브 모듈 연동이 번거롭다는 걸 알고 있었고, Flutter는 Dart지만 단일 코드베이스로 iOS/Android/Web을 모두 커버한다는 게 매력적이었습니다. 2026년 기준 Flutter의 시장 점유율이 46%로 React Native를 앞질렀다는 것도 결정에 영향을 줬습니다.

## Dart는 생각보다 쉽습니다

Dart의 첫인상은 "Java와 JavaScript를 섞어놓은 것" 같았습니다. 타입이 강하고, 클래스 기반이며, async/await를 지원합니다.

```dart
// Dart 기본 문법 — 낯설지 않습니다
void main() {
  var name = '홍길동';
  String greeting = 'Hello, $name!';
  print(greeting);
}

// 비동기 함수
Future<String> fetchUserName(int id) async {
  final response = await http.get(Uri.parse('https://api.example.com/users/$id'));
  final data = jsonDecode(response.body);
  return data['name'];
}

// Null Safety — 처음엔 당황하지만 익숙해지면 편합니다
String? nullableString = null;
String nonNullable = nullableString ?? '기본값';
```

Python에 익숙하다면 약 1주일, JavaScript를 안다면 3~4일이면 Dart 문법 자체는 이해할 수 있습니다. 어려운 건 문법보다 Flutter 위젯 시스템입니다.

## Flutter 위젯 시스템 이해하기

Flutter에서 "모든 것은 위젯"입니다. 버튼, 텍스트, 여백, 패딩, 심지어 레이아웃도 위젯입니다. 처음에는 위젯을 중첩하는 코드가 "콜백 지옥" 같아 보입니다.

```dart
// 전형적인 Flutter 위젯 중첩 구조
Scaffold(
  appBar: AppBar(title: Text('홈')),
  body: Padding(
    padding: EdgeInsets.all(16.0),
    child: Column(
      children: [
        Text('안녕하세요', style: TextStyle(fontSize: 24)),
        SizedBox(height: 16),
        ElevatedButton(
          onPressed: () => print('클릭'),
          child: Text('버튼'),
        ),
      ],
    ),
  ),
)
```

익숙해지면 이 방식이 HTML/CSS보다 직관적이라는 걸 느끼게 됩니다. 레이아웃이 코드 구조에 그대로 드러나기 때문입니다.

![Flutter 3.x 크로스플랫폼 개발 흐름](/images/flutter-dev-workflow.svg)

## 상태관리: Riverpod 선택

Flutter 상태관리는 Provider, Bloc, Riverpod, GetX 등 선택지가 많아서 처음엔 혼란스럽습니다. 여러 프로젝트를 거친 결론은 **Riverpod**입니다.

이유는 간단합니다. 컴파일 타임 안전성, 테스트 용이성, Provider의 단점을 깔끔하게 해결한 설계입니다.

```dart
// Riverpod으로 API 상태 관리
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'user_provider.g.dart';

@riverpod
Future<User> user(UserRef ref, int userId) async {
  final repository = ref.watch(userRepositoryProvider);
  return repository.fetchUser(userId);
}

// 위젯에서 사용
class UserScreen extends ConsumerWidget {
  final int userId;
  const UserScreen({required this.userId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final userAsync = ref.watch(userProvider(userId));

    return userAsync.when(
      loading: () => CircularProgressIndicator(),
      error: (err, stack) => Text('오류: $err'),
      data: (user) => Text('안녕하세요, ${user.name}님'),
    );
  }
}
```

`when()` 메서드로 로딩/에러/성공 상태를 한 번에 처리하는 패턴이 매우 편리합니다.

## 프로젝트 폴더 구조

작은 앱이라도 처음부터 구조를 잡아두는 것이 좋습니다.

```
lib/
├── main.dart
├── app/
│   ├── router.dart          # go_router 설정
│   └── theme.dart           # 테마 설정
├── features/
│   ├── auth/
│   │   ├── presentation/    # 화면 위젯
│   │   ├── domain/          # 비즈니스 로직
│   │   └── data/            # API, DB 연동
│   └── home/
│       ├── presentation/
│       ├── domain/
│       └── data/
├── shared/
│   ├── widgets/             # 공통 위젯
│   └── utils/               # 유틸리티
└── core/
    ├── network/             # Dio 클라이언트
    └── storage/             # SharedPreferences
```

Feature-First 구조를 사용합니다. 기능별로 폴더를 나누면 팀 협업 시 충돌이 줄고, 나중에 특정 기능을 분리하거나 삭제하기도 쉽습니다.

## 자주 쓰는 패키지 목록

```yaml
# pubspec.yaml
dependencies:
  flutter:
    sdk: flutter

  # 상태관리
  flutter_riverpod: ^2.5.0
  riverpod_annotation: ^2.3.0

  # 네비게이션
  go_router: ^13.0.0

  # 네트워크
  dio: ^5.4.0

  # JSON 직렬화
  json_annotation: ^4.8.0

  # 로컬 저장소
  shared_preferences: ^2.2.0

  # UI 유틸
  cached_network_image: ^3.3.0
  flutter_svg: ^2.0.0

dev_dependencies:
  build_runner: ^2.4.0
  riverpod_generator: ^2.3.0
  json_serializable: ^6.7.0
```

## Hot Reload의 생산성

Flutter 개발에서 가장 좋았던 경험은 Hot Reload입니다. 코드를 수정하고 저장하면 앱이 재시작 없이 즉시 반영됩니다. UI를 조정할 때 특히 강력합니다. 색상을 바꾸고 저장하면 100ms 안에 시뮬레이터에서 결과를 볼 수 있습니다.

React Native의 Fast Refresh와 비슷하지만, Flutter의 Hot Reload가 더 안정적이라는 느낌을 받았습니다.

## iOS/Android 빌드 및 배포

### Android 빌드

```bash
# APK (테스트용)
flutter build apk --release

# AAB (Play Store 배포용)
flutter build appbundle --release
```

`android/app/build.gradle`에서 서명 설정만 해두면 됩니다.

### iOS 빌드

iOS는 macOS와 Xcode가 필요합니다. Windows 환경에서는 CI/CD(GitHub Actions + macOS runner)를 이용하는 방법이 현실적입니다.

```bash
# iOS 빌드
flutter build ios --release
```

Apple Developer 계정, 인증서, 프로비저닝 프로파일 설정이 까다롭지만, Fastlane을 사용하면 자동화가 가능합니다.

## React Native vs Flutter 2026년 선택 기준

이 질문은 여전히 많이 받습니다. 직접 둘 다 써본 관점에서 정리합니다.

**Flutter를 선택하는 경우:**
- UI 일관성이 중요한 앱 (브랜드 가이드라인 엄수)
- iOS/Android/Web/Desktop을 모두 타겟팅
- 고성능 애니메이션, 게임 UI
- 팀에 Dart 학습 의지가 있는 경우

**React Native를 선택하는 경우:**
- 팀이 JavaScript/TypeScript에 이미 익숙한 경우
- 웹 프론트엔드 개발자가 앱도 같이 맡는 경우
- 네이티브 룩앤필이 중요한 일반적인 앱

2026년 기준으로 취업 시장에서는 Flutter 수요가 더 빠르게 늘고 있습니다. Dart를 새로 배워야 하는 초기 비용이 있지만, 투자 대비 효율은 충분합니다.

## 한 달 만에 앱 출시한 경험

Flutter로 처음 만든 앱은 IoT 기기 제어 앱이었습니다. BLE로 ESP32 기기와 통신하고, 센서 데이터를 실시간 그래프로 표시하는 기능이었습니다.

```dart
// flutter_blue_plus로 BLE 통신
final subscription = FlutterBluePlus.scanResults.listen((results) {
  for (ScanResult r in results) {
    if (r.device.platformName == 'MySensor') {
      r.device.connect();
      break;
    }
  }
});

FlutterBluePlus.startScan(timeout: Duration(seconds: 10));
```

하드웨어 엔지니어로서 BLE 프로토콜은 이미 알고 있었기 때문에 앱 레이어 구현에만 집중할 수 있었습니다. 기획부터 앱 스토어 출시까지 한 달 걸렸습니다. 같은 걸 네이티브(Swift + Kotlin)로 했다면 두 배는 걸렸을 겁니다.

Flutter, 생각보다 훨씬 좋습니다. Dart 거부감만 극복하면 됩니다.
