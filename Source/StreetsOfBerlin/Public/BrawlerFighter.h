#pragma once

#include "CoreMinimal.h"
#include "BrawlerEntity.h"
#include "BrawlerFighter.generated.h"

class ABrawlerGameMode;

/**
 * Gemeinsame Basis fuer Spieler und Gegner:
 * Zustandsmaschine, Angriffe mit aktiven Frames, Hitstun, Knockdown,
 * Jonglieren, Griffe/Wuerfe, Aufstehen mit Unverwundbarkeit.
 */
UCLASS(Abstract)
class STREETSOFBERLIN_API ABrawlerFighter : public ABrawlerEntity
{
	GENERATED_BODY()

public:
	ABrawlerFighter();

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Brawler")
	EBrawlerTeam Team = EBrawlerTeam::Enemy;

	/** Ordner/Praefix der Sprites, z.B. "Kai" */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Brawler")
	FString SpriteSet;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Brawler")
	FString DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Brawler")
	float MaxHealth = 100.f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Brawler")
	float Health = 100.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Brawler")
	float WalkSpeed = 250.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Brawler")
	float DepthSpeed = 160.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Brawler")
	bool bGrabbable = true;

	/** Leichte Treffer, die ohne Hitstun eingesteckt werden */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Brawler")
	int32 Armor = 0;

	EFighterState GetState() const { return State; }
	float GetStateTime() const { return StateTime; }
	bool IsAlive() const { return State != EFighterState::Dead && Health > 0.f; }
	bool IsGroundedAndFree() const { return State == EFighterState::Idle || State == EFighterState::Walk; }
	bool IsDowned() const { return State == EFighterState::Down || State == EFighterState::Falling || State == EFighterState::GetUp || State == EFighterState::Dead; }
	bool IsInvulnerable() const { return InvulnerableTimer > 0.f || (State == EFighterState::Attack && CurrentAttack.bInvulnerable && AnimFrame <= CurrentAttack.ActiveEnd); }
	const FBrawlerAttack& GetCurrentAttack() const { return CurrentAttack; }
	ABrawlerFighter* GetGrabPartner() const { return GrabPartner.Get(); }

	// ABrawlerEntity
	virtual bool IsHittable(EBrawlerTeam AttackerTeam) const override;
	virtual bool ReceiveHit(ABrawlerFighter* Attacker, const FBrawlerAttack& Attack, float Direction) override;
	virtual float GetHurtHeight() const override;

	/** Faellt zu Boden (Richtung: +1 = nach rechts wegfliegen) */
	void Knockdown(float Direction, float Speed, float Launch);

	/** Griff: this packt Target */
	void StartGrab(ABrawlerFighter* Target);
	void ReleaseGrab();
	void OnGrabbedBy(ABrawlerFighter* Grabber);
	void OnReleasedFromGrab();
	/** Wird geworfen; trifft dabei andere Figuren des eigenen Teams */
	void GetThrown(ABrawlerFighter* Thrower, float Direction);

	void MakeInvulnerable(float Seconds) { InvulnerableTimer = FMath::Max(InvulnerableTimer, Seconds); }
	void Heal(float Amount) { Health = FMath::Min(MaxHealth, Health + Amount); }

	/** Angriff beginnen */
	virtual void StartAttack(const FBrawlerAttack& Attack);

	// --- Waffen -------------------------------------------------------------
	FName GetWeapon() const { return Weapon; }
	bool HasWeapon() const { return !Weapon.IsNone(); }
	int32 GetWeaponDurability() const { return WeaponDurability; }
	/** Waffe in die Hand nehmen (Durability < 0 = Standardwert der Waffe) */
	void TakeWeapon(FName Type, int32 Durability = -1);
	/** Waffe fallen lassen (als aufhebbarer Gegenstand) */
	void DropWeapon(bool bPop = true);
	/** Waffe als Geschoss werfen */
	void ThrowWeapon();

protected:
	virtual void BeginPlay() override;
	virtual void TickEntity(float DeltaSeconds) override;

	/** Eingabe (Spieler) bzw. KI (Gegner) – nur in Idle/Walk/Jump/Grabbing aufgerufen */
	virtual void TickControl(float DeltaSeconds) {}

	/** Callbacks fuer Unterklassen */
	virtual void OnAttackHit(ABrawlerEntity* Target, const FBrawlerAttack& Attack) {}
	virtual void OnAttackFinished() {}
	virtual void OnHurt(ABrawlerFighter* Attacker, float Damage) {}
	virtual void OnDied() {}
	virtual void OnLanded();
	/** Wird waehrend eines Angriffs jeden Frame aufgerufen (z.B. Waffe loslassen) */
	virtual void OnAttackFrame();
	virtual void UpdateRender() override;
	void UseWeaponHit();

	void EnterState(EFighterState NewState);
	void PlayCharAnim(FName Anim, bool bRestart = false, float FPSOverride = 0.f);
	static void GetAnimInfo(FName Anim, float& OutFPS, bool& bOutLoop);

	void ApplyMovement(float DeltaSeconds);
	void TickAirPhysics(float DeltaSeconds);
	void TickAttack(float DeltaSeconds);
	void ProcessAttackHits();
	void ProcessThrownCollisions();
	void KeepGrabPartnerInPlace();
	void ClampPosition();

	ABrawlerGameMode* GetBrawlerGameMode() const;

	EFighterState State = EFighterState::Idle;
	float StateTime = 0.f;
	float HurtDuration = 0.3f;
	float InvulnerableTimer = 0.f;
	float DownDuration = 0.9f;
	float GetUpInvulnerability = 0.6f;
	int32 ArmorHits = 0;
	float ArmorResetTimer = 0.f;

	FBrawlerAttack CurrentAttack;
	bool bAttackConnected = false;
	int32 LastActiveFrame = -1;
	TArray<TWeakObjectPtr<ABrawlerEntity>> HitThisAttack;

	TWeakObjectPtr<ABrawlerFighter> GrabPartner;
	float GrabTimer = 0.f;

	bool bThrown = false;
	bool bBounced = false;
	TWeakObjectPtr<ABrawlerFighter> Thrower;
	TArray<TWeakObjectPtr<ABrawlerFighter>> ThrownHits;

	/** Darf die Figur den sichtbaren Bildschirmbereich verlassen (Gegner beim Betreten) */
	bool bClampToView = true;

	UPROPERTY(VisibleAnywhere, Category = "Brawler")
	TObjectPtr<UPaperSpriteComponent> WeaponSprite;

	FName Weapon;
	int32 WeaponDurability = 0;
};
