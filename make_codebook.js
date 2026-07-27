const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, AlignmentType, BorderStyle, ShadingType, LevelFormat, convertMillimetersToTwip,
} = require("docx");
const fs = require("fs");

const FONT = "Malgun Gothic";
const ACCENT = "1F4E79";
const HEAD_BG = "D9E2F3";

const p = (text, opts = {}) =>
  new Paragraph({
    children: [new TextRun({ text, font: FONT, size: opts.size || 21, bold: opts.bold, color: opts.color })],
    spacing: { after: opts.after ?? 120, line: 300 },
    ...(opts.heading ? { heading: opts.heading } : {}),
    ...(opts.numbering ? { numbering: opts.numbering } : {}),
  });

const h1 = (t) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 320, after: 160 },
  children: [new TextRun({ text: t, font: FONT, size: 28, bold: true, color: ACCENT })],
});

const h2 = (t) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 240, after: 120 },
  children: [new TextRun({ text: t, font: FONT, size: 24, bold: true, color: "333333" })],
});

const bullet = (t) => new Paragraph({
  numbering: { reference: "bullets", level: 0 },
  spacing: { after: 80, line: 300 },
  children: [new TextRun({ text: t, font: FONT, size: 21 })],
});

const num = (t, ref = "nums") => new Paragraph({
  numbering: { reference: ref, level: 0 },
  spacing: { after: 80, line: 300 },
  children: [new TextRun({ text: t, font: FONT, size: 21 })],
});

function table(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (text, isHead) => new TableCell({
    width: { size: 0, type: WidthType.AUTO },
    shading: isHead ? { type: ShadingType.CLEAR, fill: HEAD_BG } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({
      spacing: { after: 0, line: 276 },
      children: [new TextRun({ text, font: FONT, size: 19, bold: !!isHead })],
    })],
  });
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, children: headers.map((hh, i) => {
        const c = cell(hh, true); return c;
      }) }),
      ...rows.map((r) => new TableRow({ children: r.map((c) => cell(c, false)) })),
    ],
  });
}

// column-width-aware cell builder (rebuild with widths)
function tableW(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const mk = (text, w, isHead) => new TableCell({
    width: { size: w, type: WidthType.DXA },
    shading: isHead ? { type: ShadingType.CLEAR, fill: HEAD_BG } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({
      spacing: { after: 0, line: 276 },
      children: [new TextRun({ text, font: FONT, size: 19, bold: !!isHead })],
    })],
  });
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, children: headers.map((t, i) => mk(t, widths[i], true)) }),
      ...rows.map((r) => new TableRow({ children: r.map((t, i) => mk(t, widths[i], false)) })),
    ],
  });
}

const spacer = () => new Paragraph({ spacing: { after: 120 }, children: [] });

const doc = new Document({
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360, hanging: 200 } } } }] },
      { reference: "nums", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360, hanging: 260 } } } }] },
      { reference: "nums2", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360, hanging: 260 } } } }] },
    ],
  },
  styles: { default: { document: { run: { font: FONT, size: 21 } } } },
  sections: [{
    properties: {},
    children: [
      // 표지 헤더
      new Paragraph({
        spacing: { before: 200, after: 60 },
        children: [new TextRun({ text: "HR 챗봇 데이터 구축 코드북", font: FONT, size: 40, bold: true, color: ACCENT })],
      }),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun({ text: "사내규정–현행법규 매핑 및 Q&A 데이터 작성 기준", font: FONT, size: 24, color: "666666" })],
      }),
      new Paragraph({
        spacing: { after: 240 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: ACCENT } },
        children: [new TextRun({ text: "버전 0.1 (초안) | 작성일 2026-07-27 | 작성자: (팀명)", font: FONT, size: 18, color: "888888" })],
      }),

      h1("1. 문서 개요"),
      p("본 코드북은 HR 챗봇의 지식 데이터(사내규정–현행법규 매핑, Q&A 데이터)를 구축할 때 팀원 전원이 따라야 하는 분류·코딩·작성 기준을 정의한다. 여러 명이 나누어 작업하더라도 동일한 판단 기준으로 일관된 데이터를 만드는 것이 목적이다."),
      p("적용 범위: qa_data.json(Q&A 데이터), policy_law_map.json(규정–법령 매핑 테이블), 그리고 이를 생성·수정하는 모든 작업.", { after: 60 }),
      p("본 문서와 실제 데이터가 충돌하면 본 문서가 우선하며, 기준 자체를 바꿀 때는 §10 변경 이력에 기록한다."),

      h1("2. 용어 정의"),
      tableW(
        ["용어", "정의"],
        [
          ["사내규정", "회사가 자체 제정한 규범 문서(취업규칙, 복리후생규정, 보수규정, 운영지침 등)"],
          ["현행법규", "국가법령정보센터(law.go.kr) 기준 시행 중인 법령의 조문"],
          ["조항(레코드)", "매핑·출처 표시의 최소 단위. 규정은 조 단위, 법령은 조·항 단위로 분해"],
          ["매핑", "사내규정 조항 1건에 근거 법령 조항을 연결하고 관계 유형을 부여하는 작업"],
          ["Q&A 항목", "대표 질문 + 유사표현 + 답변 + 출처(규정/법령)로 구성된 챗봇 지식 1건"],
          ["유사표현(paraphrase)", "같은 답을 요구하는 다른 말투·어휘의 질문 문장"],
        ],
        [1800, 7200],
      ),

      h1("3. 카테고리 분류 기준"),
      p("모든 Q&A 항목은 아래 4개 카테고리 중 정확히 하나에 속한다. 경계 사례는 '분류 규칙' 열을 우선 적용한다."),
      tableW(
        ["카테고리(id)", "포함", "제외 및 분류 규칙"],
        [
          ["연차/휴가 (leave)", "연차 발생·사용·이월, 반차, 병가, 공가", "경조휴가는 welfare로 분류(경조 사건 기준 우선)"],
          ["복리후생/경조사 (welfare)", "경조금, 경조휴가, 학자금, 건강검진, 동호회 지원", "출산휴가·육아휴직은 leave로 분류(법정 휴가 우선)"],
          ["급여/수당 (salary)", "급여일, 상여, 연장·야간·휴일수당, 퇴직금, 4대보험 공제", "복리후생성 금품(경조금 등)은 welfare"],
          ["기타 (etc)", "재택·유연근무, 복장, 증명서 발급, 위 3개에 속하지 않는 것", "어디에도 애매하면 etc가 아니라 '보류' 처리 후 회의에서 확정(§7)"],
        ],
        [2100, 3600, 3300],
      ),
      p("공통 원칙: 하나의 질문이 두 카테고리에 걸치면 사용자가 궁금해하는 '결과' 기준으로 분류한다. 예: \"결혼하면 휴가랑 돈 얼마나 나와요?\" → 사건(경조) 기준 welfare.", { after: 200 }),

      h1("4. 사내규정–법령 관계 유형"),
      p("매핑 레코드마다 관계 유형(relation)을 반드시 1개 부여한다."),
      tableW(
        ["코드", "유형", "정의", "예시"],
        [
          ["L1", "법정의무", "법령상 의무를 그대로 반영한 조항", "연차 15일 = 근로기준법 제60조"],
          ["L2", "법정기준 상회", "법정 최저 기준보다 유리하게 정한 조항", "배우자 출산휴가 10일+α, 법정 외 유급휴가 추가"],
          ["L3", "법정의무 없음", "법령에 근거가 없는 회사 자체 제도", "경조금, 재택근무, 동호회 지원"],
          ["L4", "법정기준 미달 의심", "법정 기준보다 불리해 보이는 조항(검토 필요 플래그)", "연차 사용 제한이 근기법 제60조 제5항과 충돌 의심"],
        ],
        [700, 1800, 3600, 2900],
      ),
      h2("판정 절차"),
      num("조항의 핵심 주제어로 관련 법령 후보를 검색한다(근로기준법 → 남녀고용평등법 → 퇴직급여법 → 최저임금법 → 고용보험법 순으로 확인)."),
      num("해당 조문이 있으면 사내 기준과 법정 기준을 비교해 L1/L2/L4 중 판정한다."),
      num("어느 법령에서도 근거 조문을 찾지 못하면 L3으로 분류하되 verified=false로 표시하고 2차 검토를 받는다."),
      num("L4는 담당자(교수·멘토·인사팀) 확인 전까지 챗봇 답변에 노출하지 않는다."),
      p("챗봇 답변 규칙: L1·L2는 \"사내규정 + 근거 법령\"을 함께 표시하고, L3은 \"법정 제도가 아닌 회사 자체 제도\"임을 명시한다.", { after: 200 }),

      h1("5. ID 및 표기 규칙"),
      tableW(
        ["대상", "형식", "예시"],
        [
          ["Q&A 항목", "{카테고리id}-{3자리 일련번호}", "leave-001, welfare-002"],
          ["사내규정 조항", "{문서약칭}-{조}[-{항}]", "취업규칙-30, 보수규정-12-1"],
          ["법령 조항", "{법령약칭}-{조}[-{항}]", "근기법-60, 남녀고용평등법-18의2"],
          ["매핑 레코드", "{규정ID}__{법령ID}", "취업규칙-30__근기법-60"],
        ],
        [2200, 3400, 3400],
      ),
      p("법령 약칭은 근로기준법=근기법, 남녀고용평등과 일·가정 양립 지원에 관한 법률=남녀고용평등법, 근로자퇴직급여 보장법=퇴직급여법으로 통일한다. 조문 인용은 국가법령정보센터 원문을 그대로 복사하고 임의로 요약하지 않는다.", { after: 200 }),

      h1("6. 매핑 작업 절차 (반자동)"),
      num("분해: 사내규정 문서를 조 단위 레코드로 분해해 policy_articles.json에 저장한다.", "nums2"),
      num("법령 수집: law.go.kr Open API로 대상 법령 조문을 조·항 단위로 수집한다.", "nums2"),
      num("후보 추천: 유사도 매칭 엔진으로 규정 조항별 법령 후보 상위 5개를 추출한다.", "nums2"),
      num("확정: 작업자가 후보 중 근거 조문을 선택하고 관계 유형(L1~L4)을 부여한다. 추천에 없으면 직접 검색해 연결한다.", "nums2"),
      num("교차 검증: 다른 팀원 1인이 전체 매핑의 20% 이상을 무작위 재검토한다. 불일치율 10% 초과 시 기준을 회의로 재정비하고 전체 재검토한다.", "nums2"),
      p("교차 검증 결과(일치율)는 보고서의 데이터 신뢰도 근거로 기록한다.", { after: 200 }),

      h1("7. 판단 곤란 사례 처리"),
      bullet("판단이 서지 않는 레코드는 status=보류 태그를 달고 임의로 분류하지 않는다."),
      bullet("보류 항목은 주간 회의에서 합의로 확정하고, 결정 근거를 본 코드북 §10에 1줄로 남긴다."),
      bullet("동일 유형의 보류가 3회 이상 반복되면 분류 기준(§3, §4)에 규칙을 추가한다."),
      bullet("법령 개정이 확인되면 해당 매핑 전체를 재검토하고 법령 시행일 기준으로 갱신한다."),

      h1("8. Q&A 데이터 작성 규칙"),
      bullet("유사표현은 항목당 최소 5개, 권장 8개 이상. 존댓말/반말, 명사형/문장형, 동의어(연차↔휴가, 야근↔연장근무)를 섞어 작성한다."),
      bullet("답변은 3~5문장, 두괄식(결론 먼저)으로 작성하고 수치·기한을 반드시 포함한다."),
      bullet("모든 답변에 출처를 표기한다: 사내규정 조항 + 관계 유형에 따른 법령 조항(§4 규칙)."),
      bullet("개인별로 달라지는 값(잔여 연차 등)은 답변에 쓰지 않고 버튼형 조회 기능으로 연결한다."),
      bullet("추측성 표현(\"~일 것입니다\") 금지. 데이터에 없는 내용은 답변하지 않는 것이 원칙이다."),

      h1("9. 데이터 스키마"),
      p("매핑 테이블(policy_law_map.json) 레코드 예시:", { after: 60 }),
      new Paragraph({
        spacing: { after: 200 },
        shading: { type: ShadingType.CLEAR, fill: "F2F2F2" },
        children: [new TextRun({
          text: '{ "map_id": "취업규칙-30__근기법-60", "policy_id": "취업규칙-30", "policy_text": "...", "law_id": "근기법-60", "law_text": "...", "relation": "L1", "verified": true, "coder": "홍길동", "date": "2026-07-27" }',
          font: "Consolas", size: 17,
        })],
      }),
      p("coder(작업자)와 date를 반드시 기록한다. 교차 검증과 책임 추적의 기준이 된다."),

      h1("10. 버전 관리 및 변경 이력"),
      tableW(
        ["버전", "일자", "변경 내용", "작성자"],
        [
          ["0.1", "2026-07-27", "초안 작성", "(팀명)"],
          ["", "", "", ""],
          ["", "", "", ""],
        ],
        [1000, 1600, 4800, 1600],
      ),
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(__dirname + "/코드북_초안.docx", buf);
  console.log("done");
});
