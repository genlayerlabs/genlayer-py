# CHANGELOG

<!-- version list -->

## v0.8.0 (2025-07-23)

### Documentation

- Full transaction param
  ([`b55f45c`](https://github.com/genlayerlabs/genlayer-py/commit/b55f45c33e428cfa1615e1e0ba8626edca8f738d))

### Features

- Add full transaction param
  ([`0640683`](https://github.com/genlayerlabs/genlayer-py/commit/06406838fc93fa006a44e021d2fa405430dfc4b2))

### Refactoring

- Improve maintainability
  ([`a095976`](https://github.com/genlayerlabs/genlayer-py/commit/a0959766e714eb057450f6ac69cd346d0be317d6))

### Testing

- Wait for transaction receipt with real sample data
  ([`ec63e77`](https://github.com/genlayerlabs/genlayer-py/commit/ec63e77245fb2a12d992b0af7e26136a4bc4d8f2))


## v0.7.3 (2025-07-21)

### Bug Fixes

- Default transaction hash variant ([#47](https://github.com/genlayerlabs/genlayer-py/pull/47),
  [`d73f1bd`](https://github.com/genlayerlabs/genlayer-py/commit/d73f1bd1b6c62e1f635cc08ef9d70ae941b0e5fd))

### Chores

- Add ci bot to bypass branch protection
  ([`a112f41`](https://github.com/genlayerlabs/genlayer-py/commit/a112f412e81599dab236f34e8adad202fa344e8a))

### Documentation

- Update readme docs link ([#46](https://github.com/genlayerlabs/genlayer-py/pull/46),
  [`0d4c7a0`](https://github.com/genlayerlabs/genlayer-py/commit/0d4c7a065181f2057451a64b7ac27f3348feae23))


## v0.7.2 (2025-07-16)

### Bug Fixes

- Disable log messages by default
  ([`711b1e2`](https://github.com/genlayerlabs/genlayer-py/commit/711b1e23c3a8400d8761305401256ba95e1abb71))

### Documentation

- **CONTRIBUTING**: Added log configuration
  ([`d2ca2c5`](https://github.com/genlayerlabs/genlayer-py/commit/d2ca2c56ccdb614e1454d713fb768fa13889752b))


## v0.7.1 (2025-07-14)

### Bug Fixes

- Error decoding eq output
  ([`0258e7b`](https://github.com/genlayerlabs/genlayer-py/commit/0258e7b566023e845a58b782746278d5fabfbaad))


## v0.7.0 (2025-07-04)

### Bug Fixes

- Typo
  ([`037f4b1`](https://github.com/genlayerlabs/genlayer-py/commit/037f4b113de2cc1b485a469568724f5f8c1620ae))

### Features

- Add simulate write contract action
  ([`0c0503f`](https://github.com/genlayerlabs/genlayer-py/commit/0c0503f7031a51631825e8f748606a955b32e5b5))

### Testing

- Merge and add e2e tests by contract
  ([`b15be35`](https://github.com/genlayerlabs/genlayer-py/commit/b15be35c5c9162266f1a42ac1ab0d51adc351ce9))


## v0.6.1 (2025-06-27)

### Bug Fixes

- Improve error message
  ([`9a0bd96`](https://github.com/genlayerlabs/genlayer-py/commit/9a0bd96eec879b7461e57aa1214cca3437287500))


## v0.6.0 (2025-06-26)

### Bug Fixes

- Improve reliability
  ([`3206154`](https://github.com/genlayerlabs/genlayer-py/commit/32061544214ac3f9af59720dd4197adcc06ce8aa))

### Features

- Implement consensus module
  ([`9cfa9db`](https://github.com/genlayerlabs/genlayer-py/commit/9cfa9dba22d5d2a8615c7caa57ce89f55676413e))

### Refactoring

- Move files to consensus and utils
  ([`12e7caf`](https://github.com/genlayerlabs/genlayer-py/commit/12e7caf953c0868e2a3c59fa733cb8963182cc18))

- Use decoding functions
  ([`feb7a51`](https://github.com/genlayerlabs/genlayer-py/commit/feb7a51a01b8e8c2130d60ce562af8eb456acdcd))

### Testing

- Organize and test consensus main functions
  ([`4fff277`](https://github.com/genlayerlabs/genlayer-py/commit/4fff277c427d676ebabf926de5a6500aa8abe692))


## v0.5.0 (2025-06-17)

### Features

- **testnet**: Decode leader receipt
  ([`deff097`](https://github.com/genlayerlabs/genlayer-py/commit/deff09794ede3449aabe0d41d17007b66fed189b))

- **testnet**: Decode triggered transactions
  ([`5d74293`](https://github.com/genlayerlabs/genlayer-py/commit/5d742932b418c6b025d84329be99fc5550acfc4b))

### Refactoring

- Raise error on genlayer provider and simplify logic
  ([`d86cb7c`](https://github.com/genlayerlabs/genlayer-py/commit/d86cb7cd227ee0411d55c2602b07bc8fb847d592))


## v0.4.1 (2025-06-17)

### Bug Fixes

- Update testnet chain data
  ([`e852c94`](https://github.com/genlayerlabs/genlayer-py/commit/e852c941dfbdbabe36700f607bee267a778f6630))


## v0.4.0 (2025-06-10)

### Chores

- Add release setup
  ([`654e30f`](https://github.com/genlayerlabs/genlayer-py/commit/654e30f161f0e704cfd15d10684bf0fd7ed9e3b4))

- Update to 0.3.1
  ([`f3a6efe`](https://github.com/genlayerlabs/genlayer-py/commit/f3a6efe63379c636f719ce8b8f5b43d1d6cc0b7d))

### Documentation

- Add changelog
  ([`2b65915`](https://github.com/genlayerlabs/genlayer-py/commit/2b6591556a99416cbc00ad0838425ba37ca0e654))

- **contributing**: Added commit standards and versioning
  ([`a4c0495`](https://github.com/genlayerlabs/genlayer-py/commit/a4c0495199f289682c2ee68a22bd2d3e697c48bf))

### Features

- Add assertions for tx receipt
  ([`8bccce2`](https://github.com/genlayerlabs/genlayer-py/commit/8bccce247b856c264340853449f27a652903c5d6))

### Testing

- Tx receipt assertions
  ([`7f054eb`](https://github.com/genlayerlabs/genlayer-py/commit/7f054eb7e449c21e823a61d1b9c47c5caf8c3e42))


## v0.3.0 (2025-06-04)

- feat: decode new leader receipt data

## v0.2.1 (2025-05-30)

- Initial Release
