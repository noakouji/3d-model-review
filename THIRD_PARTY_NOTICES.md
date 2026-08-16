# Third Party Notices

このリポジトリには以下のサードパーティ製ソフトウェアを同梱している。

---

## three.js (r160)

- 配置: `viewer/vendor/three/`
- 対象: `three.module.js`, `addons/controls/OrbitControls.js`,
  `addons/loaders/STLLoader.js`, `addons/helpers/ViewHelper.js`
- 取得元: https://github.com/mrdoob/three.js
- ライセンス: MIT

```
The MIT License

Copyright © 2010-2023 three.js authors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 参照しているが同梱していないもの

以下はこのリポジトリに含まれない。利用する場合は各自でインストールし、
それぞれのライセンスに従うこと。

- **build123d** — Apache License 2.0 / https://github.com/gumyr/build123d
- **build123d MCP server** — モデリング手順のスキル本文は当該サーバーが配布するもので、
  このリポジトリには複製していない。`references/build123d-workflow.md` は
  このビューアと組み合わせる際の運用メモであり、独立した著作物。
